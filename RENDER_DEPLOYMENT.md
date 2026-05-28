# Upload PLPRS To GitHub And Deploy On Render

Follow these steps after the project runs locally.

## 1. Prepare Git

```powershell
git init
git add .
git commit -m "Initial PLPRS Django project"
```

## 2. Create A GitHub Repository

1. Go to https://github.com/new
2. Repository name: `plprs`
3. Choose Public or Private
4. Do not add README, `.gitignore`, or license because this project already has files
5. Click Create repository

GitHub will show commands. Use the HTTPS commands, similar to:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/plprs.git
git push -u origin main
```

## 3. Deploy On Render With Blueprint

1. Go to https://dashboard.render.com
2. Connect your GitHub account
3. Open Blueprints
4. Click New Blueprint Instance
5. Select your `plprs` repository
6. Render will detect `render.yaml`
7. Click Apply

Render will create:

- A Django web service named `plprs`
- A PostgreSQL database named `plprs-db`
- Environment variables for secret key, debug mode, and database URL

## 4. Manual Render Setup Alternative

If you do not use Blueprint:

1. Create a Render PostgreSQL database
2. Create a new Render Web Service from your GitHub repo
3. Runtime: Python 3
4. Build Command:

```bash
bash build.sh
```

5. Start Command:

```bash
gunicorn plprs_project.wsgi:application
```

6. Add environment variables:

```text
DJANGO_SECRET_KEY=<generate secure value>
DJANGO_DEBUG=False
DATABASE_URL=<your Render PostgreSQL internal database URL>
WEB_CONCURRENCY=4
```

## 5. Create Admin User On Render

After deployment, open the Render Shell for your web service and run:

```bash
python manage.py createsuperuser
```

Then open:

```text
https://your-service-name.onrender.com/admin/
```

## 6. Common Deployment Fixes

If you see `DisallowedHost`, check `RENDER_EXTERNAL_HOSTNAME` or set:

```text
DJANGO_ALLOWED_HOSTS=your-service-name.onrender.com
```

If tables are missing, run in Render Shell:

```bash
python manage.py migrate
python manage.py seed_demo_data
```

If static files are missing, redeploy and confirm the build command is:

```bash
bash build.sh
```
