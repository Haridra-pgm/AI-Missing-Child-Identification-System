# AI Missing Child Identification System

An AI-powered web application designed to assist in the identification and tracing of missing children using facial recognition, image matching, case management, location information, and AI-based age progression.

The system provides dedicated portals for **parents/guardians, child finders, and authorities**, allowing missing-child cases to be registered, searched, monitored, and managed through a centralized application.

> **Project Type:** AI / Machine Learning / Computer Vision / Web Application
> **Interface:** Streamlit
> **Database:** SQLite
> **License:** MIT

---

## 📌 Overview

The **AI Missing Child Identification System** aims to provide a technology-driven approach for supporting missing-child identification.

A registered child's photographs are processed using face detection and facial feature extraction. The generated face embeddings are stored in the database and can later be compared against an uploaded image of a found child.

The system ranks potential matches using facial embedding similarity and provides relevant case information to authorized users.

The project also includes an **AI-based age progression feature**, which generates an estimated future appearance of a child to assist with identification when a significant amount of time has passed.

---

## 🎯 Objectives

* Assist in identifying missing children using facial recognition.
* Generate and store facial embeddings from registered child images.
* Compare uploaded found-child images with registered missing-child records.
* Rank potential matches using similarity scores.
* Maintain structured missing-child case records.
* Provide separate interfaces for parents, child finders, and authorities.
* Record found-child reports and their possible matches.
* Provide location information related to missing-child cases.
* Generate AI-based age-progressed estimates for older appearances.
* Maintain case timelines, search history, notifications, and activity logs.
* Provide a centralized and organized platform for missing-child case management.

---

## ✨ Key Features

### 1. 👤 Missing Child Registration

Authorities or authorized users can register a missing-child case with:

* Child's full name
* Age
* Gender
* Identification marks
* Additional description
* Last-seen location
* Last-seen date and time
* Parent/guardian information
* Contact information
* Address
* Government ID information
* Multiple child photographs

Uploaded images are validated before being processed for facial embeddings.

---

### 2. 🤖 AI Facial Recognition

The system uses computer vision techniques to generate facial embeddings.

The current implementation uses:

* **OpenCV YuNet** for face detection
* **OpenCV SFace** for face feature extraction
* Image-quality evaluation
* Face confidence checking
* Face-size validation
* Embedding normalization

The system rejects unsuitable images such as images with no detectable face, multiple faces, low-quality faces, or faces that are too small.

---

### 3. 🔍 Found Child Image Matching

A user can upload an image of a found child for searching.

The system:

1. Validates the uploaded image.
2. Checks image quality.
3. Detects the face.
4. Generates a facial embedding.
5. Retrieves registered child embeddings.
6. Calculates similarity scores.
7. Ranks potential matches.
8. Applies a similarity threshold.
9. Displays the best potential matches.

The matching system uses normalized facial embeddings and cosine similarity for ranking candidates.

---

### 4. 🧒 AI Age Progression

The system includes an AI-based age progression module that can generate an estimated future appearance of a registered child.

The feature allows an authorized user to:

* Select a missing-child case.
* Select a source photograph.
* Select a target age.
* Generate an age-progressed image.
* Evaluate identity preservation.
* Save the generated result.
* Maintain age-progression history.

The generated image is treated as an **estimate only**, not as an exact prediction or confirmed identity.

---

### 5. 👥 Role-Based Portals

The application provides different interfaces depending on the user's role.

#### Parent / Guardian

* Parent dashboard
* Register missing child
* View linked case information
* Access case details through QR-based links

#### Child Finder

* Child Finder dashboard
* Report a found child
* Search for potential child matches

#### Authority

* Authority dashboard
* Register missing children
* View records
* Search for found children
* AI age progression
* Admin dashboard
* Manage and monitor case information

These role-based navigation flows are implemented in the main Streamlit application.

---

### 6. 📍 Location Support

The system stores the last-seen location of a missing child along with latitude and longitude information.

Location information can be used for:

* Case management
* Map visualization
* Last-seen location tracking
* Found-child reports

The project uses **Folium** and **streamlit-folium** for map-related functionality.

---

### 7. 📱 QR-Based Case Access

The application includes QR-code functionality for case-related information.

A QR-linked case can allow authorized users to access relevant case details directly through the application.

---

### 8. 📝 Found Child Reports

Child finders can submit reports containing information such as:

* Found-child image
* Location
* Description
* Potential matching records
* Similarity information

Reports are stored and can be reviewed through the authority-side workflow.

---

### 9. 📊 Dashboards

The application provides dashboards for different user roles.

Dashboards can be used to view and manage:

* Missing-child records
* Found-child reports
* Case information
* Matching results
* Activity information
* Notifications
* Case timelines

---

### 10. 🕒 Case Timeline

The system maintains timeline events related to missing-child cases.

This helps track important activities and updates associated with a case.

---

### 11. 🔔 Notifications

The database supports notifications associated with:

* Users
* Cases
* Found-child reports
* Case updates

Notifications can be associated with specific users or roles.

---

### 12. 📜 Search & Activity History

The application maintains records of:

* Image searches
* Matching results
* Search status
* Similarity scores
* Application activities
* Case-related events

This provides a structured history of system activity.

---

## 🧠 AI / Computer Vision Pipeline

```text
                Child Image
                     │
                     ▼
             Image Validation
                     │
                     ▼
            Image Quality Check
                     │
                     ▼
             Face Detection
             (OpenCV YuNet)
                     │
                     ▼
             Face Alignment
                     │
                     ▼
          Face Feature Extraction
             (OpenCV SFace)
                     │
                     ▼
            Face Embedding
                     │
                     ▼
        Store / Compare Embedding
                     │
                     ▼
          Cosine Similarity
                     │
                     ▼
          Rank Potential Matches
                     │
                     ▼
           Display Top Matches
```

The implementation performs image-quality checks, face detection, embedding generation, normalization, and similarity-based ranking.

---

## 🏗️ System Architecture

```text
┌───────────────────────────────────────────────┐
│                 Streamlit UI                  │
│                                               │
│ Parent Portal │ Finder Portal │ Authority UI │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                 Services Layer                │
│                                               │
│ Authentication │ Registration │ Matching      │
│ Dashboard │ Reports │ Location │ QR │ Timeline│
└───────────────────────┬───────────────────────┘
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
┌──────────────────────┐  ┌────────────────────┐
│   AI / CV Modules    │  │   SQLite Database  │
│                      │  │                    │
│ YuNet Face Detection │  │ Users              │
│ SFace Embeddings     │  │ Missing Children   │
│ Age Progression      │  │ Child Images      │
│ Image Quality        │  │ Embeddings         │
│ Similarity Matching  │  │ Reports            │
└──────────────────────┘  │ Logs / Timeline    │
                          │ Notifications      │
                          └────────────────────┘
```

---

## 📁 Project Structure

```text
AI-Missing-Child-Identification-System/
│
├── .streamlit/
│   └── config.toml
│
├── ai/
│   ├── __init__.py
│   ├── age_progression_generator.py
│   ├── embedding_generator.py
│   └── model_assets.py
│
├── assets/
│   └── app_logo.svg
│
├── config/
│   ├── __init__.py
│   ├── constants.py
│   └── settings.py
│
├── database/
│   ├── __init__.py
│   ├── connection.py
│   ├── schema.py
│   └── repositories/
│
├── scripts/
│   ├── age_progression_verify.py
│   ├── phase4a_health_check.py
│   ├── phase4a_sample_registration.py
│   ├── phase4b_verify_registration.py
│   ├── phase5_verify_matching.py
│   └── phase6_verify_dashboard.py
│
├── services/
│   ├── auth_service.py
│   ├── dashboard_service.py
│   ├── embedding_service.py
│   ├── location_service.py
│   ├── matching_service.py
│   ├── qr_service.py
│   ├── records_service.py
│   ├── registration_service.py
│   ├── role_dashboard_service.py
│   └── timeline_service.py
│
├── ui/
│   ├── age_progression_ui.py
│   ├── auth_ui.py
│   ├── dashboard_ui.py
│   ├── found_report_ui.py
│   ├── location_map_ui.py
│   ├── police_station_ui.py
│   ├── qr_ui.py
│   ├── records_ui.py
│   ├── registration_ui.py
│   ├── role_dashboards_ui.py
│   ├── search_ui.py
│   ├── theme.py
│   └── timeline_ui.py
│
├── utils/
│   ├── file_handler.py
│   ├── logger.py
│   └── validators.py
│
├── .env.example
├── .gitignore
├── app.py
└── requirements.txt
```

---

## 🛠️ Technologies Used

| Technology           | Purpose                              |
| -------------------- | ------------------------------------ |
| **Python**           | Core application development         |
| **Streamlit**        | Web application interface            |
| **OpenCV**           | Computer vision and face processing  |
| **YuNet**            | Face detection                       |
| **SFace**            | Face feature extraction / embeddings |
| **PyTorch**          | AI/ML framework support              |
| **NumPy**            | Numerical operations                 |
| **Pillow**           | Image processing                     |
| **SQLite**           | Database management                  |
| **Folium**           | Interactive maps                     |
| **Streamlit-Folium** | Map integration with Streamlit       |
| **QR Code**          | QR-based case access                 |
| **Requests**         | HTTP/API communication               |
| **python-dotenv**    | Environment configuration            |
| **Replicate**        | AI model/API integration             |

These dependencies are defined in the project's `requirements.txt`.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/Haridra-pgm/AI-Missing-Child-Identification-System.git
```

### 2. Navigate into the project

```bash
cd AI-Missing-Child-Identification-System
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv venv
```

### 4. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Configuration

The project includes an `.env.example` file.

Create your local environment file:

```bash
copy .env.example .env
```

Then configure the required environment variables.

> **Never upload your actual `.env` file or API keys to GitHub.**

The `.gitignore` file is configured to exclude `.env`.

---

## ▶️ Running the Application

Start the Streamlit application using:

```bash
streamlit run app.py
```

The application will start locally and provide a URL that can be opened in a web browser.

---

## 🔎 How the Matching System Works

When a found-child image is uploaded:

```text
Upload Image
     ↓
Validate Image
     ↓
Check Image Quality
     ↓
Detect Face
     ↓
Generate Face Embedding
     ↓
Retrieve Stored Embeddings
     ↓
Normalize Embeddings
     ↓
Calculate Cosine Similarity
     ↓
Rank Candidates
     ↓
Apply Similarity Threshold
     ↓
Display Potential Matches
```

The matching service ranks candidates according to similarity and returns the highest-ranking potential matches that satisfy the configured threshold.

---

## 🗄️ Database

The application uses SQLite for persistent data storage.

The database contains structures for:

* Users
* Missing children
* Parent/guardian details
* Child images
* Face embeddings
* Activity logs
* Search history
* Found-child reports
* Found-child report matches
* Case timeline events
* Notifications
* Age progression history

This allows the application to maintain both the AI-related information and the associated case-management data.

---

## 🔒 Privacy & Responsible Use

This project deals with highly sensitive information involving children and biometric data.

For demonstration and educational purposes:

* Do not upload real children's photographs to a public repository.
* Do not commit personal information to GitHub.
* Do not commit government identification information.
* Do not commit passwords, API keys, or other credentials.
* Use synthetic, anonymized, or authorized test data when possible.
* Follow applicable privacy, data-protection, and child-safety regulations when deploying the system.
* AI-generated age-progressed images should be treated only as estimates.
* Facial similarity results should be treated as potential matches, not definitive identification.

The system's age-progression implementation itself includes a disclaimer that generated images represent possible appearances and should not be treated as confirmed identity or exact prediction.

---

## ⚠️ Limitations

* Facial recognition performance depends on image quality and lighting.
* Blurred, low-resolution, occluded, or unsuitable images may be rejected.
* Multiple faces in a search image may prevent matching.
* Facial similarity does not guarantee that two images represent the same person.
* Age progression is an estimated visualization and may not accurately represent future appearance.
* The system should support, rather than replace, official investigation and verification procedures.
* Production deployment would require stronger security, privacy controls, authentication, auditing, and infrastructure.

---

## 🚀 Future Enhancements

Possible future improvements include:

* Real-time camera-based identification.
* Improved face recognition models.
* Larger-scale vector databases for faster matching.
* Cloud deployment.
* Mobile application support.
* Advanced notification and alert systems.
* Improved geospatial analysis.
* Multi-image and video-based search.
* More robust identity verification workflows.
* Enhanced security and access-control mechanisms.
* Integration with authorized law-enforcement systems.
* Improved AI age-progression models.
* Performance optimization for large databases.

---

## 👥 Team

This project was developed as a **collaborative project**.

### Contributors

* **Haridra-pgm**
* **Srusthi-codes**

Repository collaboration and contributions can be viewed through the GitHub repository history.

---

## 📚 Project Purpose

This project was developed as an academic/technical project to explore the application of:

* Artificial Intelligence
* Machine Learning
* Computer Vision
* Facial Recognition
* Image Processing
* Database Management
* Web Application Development

It demonstrates how AI and software engineering techniques can be combined to build a prototype system for a real-world social problem.

---

## 📄 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for more information.

---

## ⭐ Acknowledgement

This project uses open-source technologies and libraries including **Python, Streamlit, OpenCV, PyTorch, NumPy, Pillow, SQLite, Folium**, and related packages.

---

## 📌 Disclaimer

This project is intended for **educational and research purposes**.

The system provides potential matches based on computational similarity and should not be considered a definitive identity-verification system. Any real-world deployment involving children, biometric information, or personal data must follow appropriate legal, ethical, privacy, and security requirements.
