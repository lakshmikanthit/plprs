# PLPRS - Personalized Learning Path Recommendation System

PLPRS is a Django starter project for student skill assessment, personalized learning paths, course/resource recommendations, progress tracking, and admin management. It uses Django, PostgreSQL, Bootstrap, and Python ML libraries.

The code in this folder is a runnable foundation. Install dependencies, connect PostgreSQL, migrate, seed demo data, and then extend the recommendation engine with your own training data.

## 1. Project Setup

```powershell
cd "C:\Users\LAKSHMIKANTH S\Documents\Codex\2026-05-18\files-mentioned-by-the-user-chatgpt"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

If `python` is not available on Windows, install Python 3.12+ from python.org and enable "Add python.exe to PATH" during installation.

## 2. PostgreSQL Configuration

Create a PostgreSQL database and user:

```sql
CREATE DATABASE plprs_db;
CREATE USER plprs_user WITH PASSWORD 'strong_password';
ALTER ROLE plprs_user SET client_encoding TO 'utf8';
ALTER ROLE plprs_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE plprs_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE plprs_db TO plprs_user;
```

Create your environment file:

```powershell
Copy-Item .env.example .env
```

Update `.env` with your database credentials.

This project keeps a SQLite fallback for quick local inspection, but the intended database engine is:

```python
django.db.backends.postgresql
```

## 3. Django Project And Apps

Project package:

```text
plprs_project/
  settings.py
  urls.py
  asgi.py
  wsgi.py
```

Apps:

```text
accounts/          registration, login, student profile
learning/          skills, courses, assessments, paths, progress
recommendations/   content, NLP, KNN, collaborative, skill-gap, adaptive, ACO logic
templates/         Bootstrap HTML templates
static/css/        dashboard styling
```

Equivalent creation commands for a fresh manual build:

```powershell
django-admin startproject plprs_project .
python manage.py startapp accounts
python manage.py startapp learning
python manage.py startapp recommendations
```

## 4. Database Migration

```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo_data
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## 5. Main Models

`StudentProfile`
: Stores learner interests, target role, and experience level.

`Skill`, `StudentSkill`, `IndustrySkillRequirement`
: Power skill assessment and skill gap analysis.

`Course`, `CourseSkill`, `Resource`
: Store course metadata, skill coverage, and external learning resources.

`AssessmentQuestion`, `AssessmentAttempt`, `AssessmentAnswer`
: Capture skill assessment results.

`LearningPath`, `LearningPathItem`, `CourseProgress`
: Track personalized paths and learner progress.

`ResourceInteraction`, `Feedback`
: Capture behavior for collaborative and adaptive recommendations.

## 6. Authentication Flow

Authentication uses Django's built-in auth views plus a custom registration form:

```text
/accounts/register/  student registration
/accounts/login/     login
/accounts/logout/    logout
/accounts/profile/   profile update
```

After login, users are redirected to `/dashboard/`.

## 7. Algorithms Used In PLPRS

Content-Based Filtering
: Builds a learner profile from interests, goals, skills, and completed courses. It compares that profile to course text and skill metadata using TF-IDF cosine similarity.

Machine Learning Recommendation Algorithm
: Combines multiple model signals into a weighted score. The service layer is designed so real trained models can be loaded later.

NLP Algorithm
: Uses spaCy, when available, to extract meaningful tokens from learner goals and course descriptions. It falls back to keyword matching if the spaCy model is not installed.

K-Nearest Neighbors
: Builds student-skill vectors, finds similar learners, and boosts courses completed or started by similar users.

Deep Learning Algorithm
: Included as a pluggable scoring hook. Add TensorFlow or PyTorch later if your dataset is large enough; the current stack intentionally avoids pretending a deep model exists before training data is available.

Collaborative Filtering
: Uses similar learner activity and progress history to recommend courses that worked for comparable students.

Skill Gap Analysis
: Compares current student proficiency with target-role skill requirements and recommends courses that close missing skills first.

Adaptive Learning
: Adjusts difficulty and next steps based on assessment score, progress, and course completion status.

Ant Colony Optimization
: Orders recommended courses into an efficient path by balancing score, prerequisites, pheromone updates, and route quality.

## 8. Recommended Development Order

1. Configure PostgreSQL and run migrations.
2. Seed demo skills, courses, resources, and assessment questions.
3. Register a student.
4. Complete the skill assessment.
5. Review the generated learning path.
6. Add more course data in Django admin.
7. Tune the weights in `recommendations/services.py`.
8. Add real event data for collaborative filtering.
9. Add a trained deep learning model only after enough data exists.

## 9. Deployment Checklist

For production:

```powershell
python manage.py check --deploy
python manage.py collectstatic
```

Set these environment variables on your host:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=plprs_db
DB_USER=plprs_user
DB_PASSWORD=strong_password
DB_HOST=your-postgres-host
DB_PORT=5432
```

Typical deployment stack:

```text
PostgreSQL + Gunicorn + Nginx + HTTPS
```

Example Gunicorn command:

```powershell
gunicorn plprs_project.wsgi:application --bind 0.0.0.0:8000
```

On platforms like Render, Railway, Azure App Service, or DigitalOcean, use the same environment variables, run migrations during release, and configure static file serving.

Official Django references used for this scaffold:

- https://docs.djangoproject.com/en/5.2/
- https://docs.djangoproject.com/en/5.2/ref/settings/
- https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/
