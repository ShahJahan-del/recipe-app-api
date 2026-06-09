# School Management System (SMS) API

A robust, containerized RESTful API designed for managing school operations, including departments, courses, student profiles, teacher assignments, and course enrollments.

This project is built using **Django Rest Framework (DRF)**, backed by a cloud-hosted **Supabase (PostgreSQL)** database, fully containerized with **Docker**, and deployed on an **AWS EC2** instance behind an **Nginx** reverse proxy.

---

## Architecture Overview

The application follows a modern, production-ready infrastructure split into containerized services managed by Docker Compose:

* **Application Server (`app`):** WSGI server running Python 3.12 and Django. Handles core business logic, permissions, and database operations.
* **Reverse Proxy (`proxy`):** Powered by Nginx. It acts as the gateway, efficiently managing static files and routing incoming HTTP traffic to the Django container.
* **Database Service:** Hosted externally on **Supabase** (Managed PostgreSQL) to guarantee high availability and data persistence away from the compute instance.

---

## Live Demo & API Access

The system is deployed and fully accessible on the internet.

* **API Base URL:** `ec2-13-48-5-192.eu-north-1.compute.amazonaws.com`
* **Django Admin Panel:** `ec2-13-48-5-192.eu-north-1.compute.amazonaws.com/admin`

### Test Credentials

To ease the evaluation process, you can use the following pre-configured roles to test the endpoint restriction and isolation logic:

| Role | Email / Username | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@example.com` | `admin` | Full CRUD on all endpoints, user creation |
| **Teacher** | `teacher@example.com` | `teacher` | Read-only courses, view specific student rosters |
| **Student** | `student@example.com` | `student` | View/update own profile, view personal enrollments |

---

## Core Security & Business Logic Features

* **Role-Based Access Control (RBAC):** Customized `get_permissions` and `get_queryset` hooks filter data dynamically based on the authenticated user's email matching their profile.
* **Data Isolation:** Students can only view their own profile; teachers can only see rosters for courses they instruct. The Admin bypasses all restrictions (`is_superuser`).
* **Automated Email Notifications:** Native Django integration triggers automated notification emails (via `send_mail`) upon new course assignments, successful student enrollments, or class unenrollments.
* **Data Integrity Check:** The `AdminUserManagementViewSet` forces structural data synchronization between Django’s authentication system (`core_user`) and Supabase application tables.


---

## Local Development Setup (with Docker)

Thanks to Docker, you can replicate the exact production environment locally on your machine with a single command.

### Prerequisites
* Docker & Docker Compose installed.
* A `.env` file containing database connection strings.

### Step-by-Step Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/ShahJahan-del/recipe-app-api.git
    cd recipe-app-api
    ```

2.  **Environment Variables Configuration:**
    Create a `.env` file in the root directory (make sure it mimics `.env.sample` but contains your Supabase credentials):
    ```env
    DB_HOST=your-supabase-db-host
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASS=your-secure-password
    DB_PORT=5432
    SECRET_KEY=your-django-secret-key
    ALLOWED_HOSTS=localhost,127.0.0.1
    ```

3.  **Spin up the Containers:**
    Run the production-ready orchestration setup:
    ```bash
    docker-compose -f docker-compose-deploy.yml up --build -d
    ```

4.  **Sync the Database:**
    Since the application tables are already on Supabase, synchronize Django’s tracking state and build the authentication schema safely using:
    ```bash
    docker-compose -f docker-compose-deploy.yml run --rm app python manage.py migrate sms_api --fake-initial
    docker-compose -f docker-compose-deploy.yml run --rm app python manage.py migrate
    ```

5.  **Create a Local Superuser (Optional):**
    ```bash
    docker-compose -f docker-compose-deploy.yml run --rm app python manage.py createsuperuser
    ```

The local API will now be listening seamlessly at `http://localhost`.

---

## API Endpoints Reference

| Endpoint | Allowed HTTP Methods | Description |
| :--- | :--- | :--- |
| `/api/departments/` | `GET`, `POST`, `PUT`, `DELETE` | Managing university faculties (Admin Only). |
| `/api/courses/` | `GET`, `POST`, `PUT`, `DELETE` | System courses. Teachers see assigned courses only. |
| `/api/students/` | `GET`, `POST`, `PUT`, `PATCH` | Student directory. Strict field locks applied to student self-updates. |
| `/api/teachers/` | `GET`, `POST`, `PUT` | Teacher data. Modification of emails is forbidden. |
| `/api/enrollments/` | `GET`, `POST`, `DELETE` | Handles class signups. Triggers administrative emails. |
| `/api/admin-management/`| `GET`, `POST`, `DELETE` | Profile generator. Auto-links Django auth users to metadata profiles. |