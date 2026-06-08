# College Management System

A Django-based College Management System designed to handle student and faculty portals with dedicated dashboards, attendance tracking, results management, and a notice system.

- Developed during an internship at BrainyBeam Info-Tech Pvt Ltd

## 🚀 Features

- **Dual Portals:** Separate login systems for Students and Faculty.
- **Attendance & Results:** Faculty can mark attendance and upload student grades.
- **Notice System:** Scoped notices based on department and semester.
- **Content Store:** Centralized repository for notes, syllabus, and resources.
- **Messaging:** Students can send inquiries to faculty, students, or admin.
- **Responsive UI:** Built with a clean "Blue Eclipse" theme.

## 🛠 Tech Stack

- **Backend:** Django
- **Database:** SQLite3
- **Styling:** CSS (Blue Eclipse Theme)
- **Admin:** Django Unfold (Tailwind CSS)

## 📋 Prerequisites

- Python 3.12+
- `pip`

## ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/your-username/college_System.git](https://github.com/your-username/college_System.git)
   cd college_System
   ```

2. **Create and activate a virtual environment:**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```

3. **Install dependencies:**
    ```bash
    pip install django django-unfold
    ```

4. **Run migrations:**
    ```bash
    python manage.py migrate
    ```

5. **Start the server:**
    ```bash
    python manage.py runserver
    ```

## 🔐 Credentials
Access the /admin/ panel using the superuser created via createsuperuser.

## 📖 Architecture
This project uses a modular design where cms/models.py defines the core data, and cms/views.py handles the business logic. All routes are defined in cms/urls.py and included in the core project.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.