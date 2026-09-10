import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

from ai.embedding_generator import FaceEmbeddingDependencyError, FaceImageRejectedError, calculate_image_quality_score
from ai.model_assets import ModelAssetError, ModelAssetSpec, ensure_model_file
from config.constants import ALLOWED_IMAGE_EXTENSIONS, MAX_CHILD_AGE, MIN_CHILD_AGE
from config.settings import (
    AGE_PROGRESSION_MODEL_NAME,
    BASE_DIR,
    MIN_FACE_AREA_RATIO,
    MIN_FACE_IMAGE_QUALITY_SCORE,
    OPENCV_FACE_NMS_THRESHOLD,
    OPENCV_FACE_SCORE_THRESHOLD,
    OPENCV_FACE_TOP_K,
    OPENCV_SFACE_MODEL_PATH,
    OPENCV_SFACE_MODEL_SHA256,
    OPENCV_SFACE_MODEL_SIZE,
    OPENCV_SFACE_MODEL_URLS,
    OPENCV_YUNET_MODEL_PATH,
    OPENCV_YUNET_MODEL_SHA256,
    OPENCV_YUNET_MODEL_SIZE,
    OPENCV_YUNET_MODEL_URLS,
)
from utils.logger import get_logger


logger = get_logger(__name__)

REPLICATE_MODEL_ID = "black-forest-labs/flux-kontext-pro"
REPLICATE_ENV_FILE = BASE_DIR / ".env"
REPLICATE_TIMEOUT_SECONDS = 90


class AgeProgressionError(Exception):
    """Raised when age progression cannot be generated."""


class AgeProgressionDependencyError(AgeProgressionError):
    """Raised when required age-progression dependencies or API credentials are unavailable."""


@dataclass(frozen=True)
class FaceAnalysis:
    image_path: str
    image_hash: str
    quality_score: float
    face_confidence: float
    face_area_ratio: float
    bbox: tuple[int, int, int, int]
    landmarks: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class AgeProgressionRenderResult:
    image_bytes: bytes
    source_analysis: FaceAnalysis
    generated_analysis: FaceAnalysis
    model_name: str
    target_age_label: str
    progression_years: int
    approach_notes: str


def ensure_age_progression_ready() -> None:
    """Validate local face-validation assets and Replicate API readiness."""
    cv2, _ = _load_cv_dependencies()
    _ensure_opencv_face_api(cv2)
    _ensure_opencv_model_assets()
    _load_required_replicate_dependencies()
    _get_replicate_api_token()
    logger.info("Replicate age progression readiness check completed")


def analyze_face_image(image_path: Path) -> FaceAnalysis:
    image_path = _validate_source_path(image_path)
    cv2, _ = _load_cv_dependencies()
    _ensure_opencv_face_api(cv2)
    _ensure_opencv_model_assets()

    quality_score = calculate_image_quality_score(image_path)
    if quality_score < MIN_FACE_IMAGE_QUALITY_SCORE:
        raise FaceImageRejectedError(
            f"Image quality score {quality_score:.1f} is below the required "
            f"{MIN_FACE_IMAGE_QUALITY_SCORE:.1f}."
        )

    image = cv2.imread(str(image_path))
    if image is None:
        raise FaceImageRejectedError("Image could not be read by OpenCV.")

    face, face_area_ratio = _detect_single_face(image)
    return FaceAnalysis(
        image_path=_relative_or_absolute_path(image_path),
        image_hash=_sha256_file(image_path),
        quality_score=quality_score,
        face_confidence=float(face[-1]),
        face_area_ratio=face_area_ratio,
        bbox=_face_bbox(face, image.shape[1], image.shape[0]),
        landmarks=_extract_landmarks(face),
    )


def generate_age_progressed_estimate(
    source_image_path: Path,
    source_age: int,
    target_age: int,
) -> AgeProgressionRenderResult:
    _validate_age_request(source_age, target_age)
    source_image_path = _validate_source_path(source_image_path)
    source_analysis = analyze_face_image(source_image_path)

    logger.info(
        "Generating Replicate age progression source_image=%s source_age=%s target_age=%s",
        source_analysis.image_path,
        source_age,
        target_age,
    )

    try:
        generated_bytes = _generate_with_replicate(source_image_path, source_age, target_age)
        image_bytes = _normalize_generated_image_bytes(generated_bytes)
        generated_analysis = _analyze_generated_bytes(image_bytes)
    except AgeProgressionError:
        raise
    except Exception as exc:
        logger.exception("Replicate age progression failed for %s", source_analysis.image_path)
        raise AgeProgressionError("Replicate age progression inference failed.") from exc

    target_age_label = age_stage_label(target_age)
    logger.info(
        "Generated Replicate age progression estimate source_age=%s target_age=%s target_stage=%s quality=%.2f",
        source_age,
        target_age,
        target_age_label,
        generated_analysis.quality_score,
    )

    return AgeProgressionRenderResult(
        image_bytes=image_bytes,
        source_analysis=source_analysis,
        generated_analysis=generated_analysis,
        model_name=AGE_PROGRESSION_MODEL_NAME,
        target_age_label=target_age_label,
        progression_years=target_age - source_age,
        approach_notes=(
            "Replicate FLUX.1 Kontext [pro] text-guided image editing is used to create a possible "
            "age-progressed portrait from the selected registered image. OpenCV YuNet and SFace are used "
            "only for face validation and identity-preservation scoring."
        ),
    )


def age_stage_label(age: int) -> str:
    if age <= 4:
        return "early childhood estimate (0-4)"
    if age <= 12:
        return "childhood estimate (5-12)"
    if age <= 19:
        return "adolescent estimate (13-19)"
    if age <= 35:
        return "young adult estimate (20-35)"
    if age <= 55:
        return "mature adult estimate (36-55)"
    return "older adult estimate (56+)"


def _generate_with_replicate(source_image_path: Path, source_age: int, target_age: int) -> bytes:
    replicate, requests = _load_required_replicate_dependencies()
    api_token = _get_replicate_api_token()
    client = replicate.Client(api_token=api_token)
    prompt = _build_age_progression_prompt(source_age, target_age)

    with source_image_path.open("rb") as image_file:
        output = client.run(
            REPLICATE_MODEL_ID,
            input={
                "input_image": image_file,
                "prompt": prompt,
                "aspect_ratio": "match_input_image",
                "output_format": "jpg",
                "safety_tolerance": 2,
                "prompt_upsampling": False,
            },
        )

    return _read_replicate_output(output, requests)


def _build_age_progression_prompt(source_age: int, target_age: int) -> str:
    return f"""
Generate the SAME person at age {target_age}.

Requirements:
- Preserve identity
- Preserve gender presentation, skin tone, face shape, eyes, nose, mouth, smile, and natural expression
- Natural aging from age {source_age} to age {target_age}
- Photorealistic portrait
- High quality
- Do not change the background more than necessary
- Do not add text, labels, watermarks, extra people, accessories, or distorted facial features
"""


def _read_replicate_output(output: Any, requests: Any) -> bytes:
    if isinstance(output, (list, tuple)):
        if not output:
            raise AgeProgressionError("Replicate returned no generated image.")
        output = output[0]

    if isinstance(output, bytes):
        return output

    if hasattr(output, "read"):
        data = output.read()
        if isinstance(data, str):
            data = data.encode("utf-8")
        if isinstance(data, bytes) and data:
            return data

    output_url = _replicate_output_url(output)
    if not output_url:
        raise AgeProgressionError("Replicate output did not include an image URL or readable image file.")

    try:
        response = requests.get(output_url, timeout=REPLICATE_TIMEOUT_SECONDS)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise AgeProgressionError("Generated image could not be downloaded from Replicate.") from exc

    if not response.content:
        raise AgeProgressionError("Downloaded Replicate image was empty.")
    return response.content


def _replicate_output_url(output: Any) -> str | None:
    if isinstance(output, str):
        return output
    url_value = getattr(output, "url", None)
    if callable(url_value):
        url_value = url_value()
    if url_value:
        return str(url_value)
    return None


def _normalize_generated_image_bytes(image_bytes: bytes) -> bytes:
    from io import BytesIO

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise AgeProgressionError("Replicate returned an unreadable or unsupported image.") from exc

    output = BytesIO()
    try:
        normalized.save(output, format="JPEG", quality=94, optimize=True)
    except OSError as exc:
        raise AgeProgressionError("Generated image could not be encoded for storage.") from exc
    return output.getvalue()


def _analyze_generated_bytes(image_bytes: bytes) -> FaceAnalysis:
    temporary_file = tempfile.NamedTemporaryFile(prefix="age_progression_validate_", suffix=".jpg", delete=False)
    temporary_path = Path(temporary_file.name)
    try:
        temporary_file.write(image_bytes)
        temporary_file.close()
        return analyze_face_image(temporary_path)
    finally:
        try:
            temporary_file.close()
            if temporary_path.exists():
                temporary_path.unlink()
        except OSError:
            logger.warning("Could not remove temporary age progression validation file: %s", temporary_path)


def _load_required_replicate_dependencies() -> tuple[Any, Any]:
    try:
        import replicate
        import requests
    except ImportError as exc:
        raise AgeProgressionDependencyError(
            "Replicate age progression dependencies are missing. Run pip install -r requirements.txt."
        ) from exc
    return replicate, requests


def _get_replicate_api_token() -> str:
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise AgeProgressionDependencyError("python-dotenv is required to load REPLICATE_API_TOKEN from .env.") from exc

    load_dotenv(REPLICATE_ENV_FILE, override=False)
    api_token = os.getenv("REPLICATE_API_TOKEN", "").strip()
    if not api_token:
        raise AgeProgressionDependencyError(
            "REPLICATE_API_TOKEN is missing. Add it to the project .env file before generating age progression."
        )
    return api_token


def _detect_single_face(image: Any) -> tuple[Any, float]:
    cv2, _ = _load_cv_dependencies()
    height, width = image.shape[:2]
    detector = cv2.FaceDetectorYN_create(
        str(OPENCV_YUNET_MODEL_PATH),
        "",
        (width, height),
        OPENCV_FACE_SCORE_THRESHOLD,
        OPENCV_FACE_NMS_THRESHOLD,
        OPENCV_FACE_TOP_K,
    )
    _, faces = detector.detect(image)
    if faces is None or len(faces) == 0:
        raise FaceImageRejectedError("No face detected.")

    valid_faces = [face for face in faces if float(face[-1]) >= OPENCV_FACE_SCORE_THRESHOLD]
    if not valid_faces:
        raise FaceImageRejectedError("No face met the minimum detection confidence.")
    if len(valid_faces) > 1:
        raise FaceImageRejectedError("Multiple faces detected. Select an image with exactly one clear child face.")

    face = valid_faces[0]
    face_area_ratio = _face_area_ratio(face, width, height)
    if face_area_ratio < MIN_FACE_AREA_RATIO:
        raise FaceImageRejectedError(
            f"Detected face is too small in the image. Face area ratio {face_area_ratio:.4f} "
            f"is below the required {MIN_FACE_AREA_RATIO:.4f}."
        )
    return face, face_area_ratio


def _extract_landmarks(face: Any) -> tuple[tuple[float, float], ...]:
    values = [float(value) for value in face[4:14]]
    return tuple((values[index], values[index + 1]) for index in range(0, len(values), 2))


def _face_bbox(face: Any, image_width: int, image_height: int) -> tuple[int, int, int, int]:
    x = max(int(round(float(face[0]))), 0)
    y = max(int(round(float(face[1]))), 0)
    width = max(int(round(float(face[2]))), 1)
    height = max(int(round(float(face[3]))), 1)
    x = min(x, image_width - 1)
    y = min(y, image_height - 1)
    width = min(width, image_width - x)
    height = min(height, image_height - y)
    return x, y, width, height


def _face_area_ratio(face: Any, image_width: int, image_height: int) -> float:
    face_width = max(float(face[2]), 0.0)
    face_height = max(float(face[3]), 0.0)
    image_area = float(image_width * image_height)
    return 0.0 if image_area <= 0 else (face_width * face_height) / image_area


def _validate_age_request(source_age: int, target_age: int) -> None:
    if source_age < MIN_CHILD_AGE or source_age > MAX_CHILD_AGE:
        raise AgeProgressionError(f"Source age must be between {MIN_CHILD_AGE} and {MAX_CHILD_AGE}.")
    if target_age < MIN_CHILD_AGE or target_age > MAX_CHILD_AGE:
        raise AgeProgressionError(f"Target age must be between {MIN_CHILD_AGE} and {MAX_CHILD_AGE}.")
    if target_age <= source_age:
        raise AgeProgressionError("Target age must be greater than the registered age.")


def _validate_source_path(image_path: Path) -> Path:
    if not image_path.exists() or not image_path.is_file():
        raise FaceImageRejectedError("Source image file is missing.")
    if image_path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise FaceImageRejectedError("Source image must be a JPEG or PNG file.")
    return image_path


def _ensure_opencv_model_assets() -> None:
    try:
        ensure_model_file(
            ModelAssetSpec(
                path=OPENCV_YUNET_MODEL_PATH,
                urls=OPENCV_YUNET_MODEL_URLS,
                sha256=OPENCV_YUNET_MODEL_SHA256,
                size_bytes=OPENCV_YUNET_MODEL_SIZE,
            )
        )
        ensure_model_file(
            ModelAssetSpec(
                path=OPENCV_SFACE_MODEL_PATH,
                urls=OPENCV_SFACE_MODEL_URLS,
                sha256=OPENCV_SFACE_MODEL_SHA256,
                size_bytes=OPENCV_SFACE_MODEL_SIZE,
            )
        )
    except ModelAssetError as exc:
        raise AgeProgressionDependencyError(str(exc)) from exc


def _load_cv_dependencies() -> tuple[Any, Any]:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise FaceEmbeddingDependencyError("OpenCV and NumPy are required for age progression validation.") from exc
    return cv2, np


def _ensure_opencv_face_api(cv2: Any) -> None:
    if not hasattr(cv2, "FaceDetectorYN_create") or not hasattr(cv2, "FaceRecognizerSF_create"):
        raise AgeProgressionDependencyError(
            "Installed OpenCV does not include YuNet/SFace APIs. Install dependencies from requirements.txt."
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_or_absolute_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(BASE_DIR))
    except ValueError:
        return str(path)
