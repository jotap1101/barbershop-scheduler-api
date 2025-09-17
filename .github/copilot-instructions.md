# AI Agent Instructions for API Codebase

This document provides essential knowledge for AI agents working with this Django-based API project.

## Project Architecture

- **Django 5.2.6 REST API** with modular structure following Django's app-based architecture
- Core configuration in `config/` directory (settings, URLs, WSGI/ASGI)
- Business logic organized in `apps/` directory following Django app structure
- Reusable utilities in `utils/` directory

### Key Components

```
.
├── apps/          # Django applications (business logic modules)
├── config/        # Core Django configuration
├── media/         # User uploaded files
└── utils/         # Shared utilities
```

## Environment & Configuration

- Environment variables managed via `django-environ`
- Required `.env` file in project root with:
  ```
  SECRET_KEY=<django-secret-key>
  DEBUG=True/False
  DB_ENGINE=django.db.backends.sqlite3
  DB_NAME=db.sqlite3
  ```
- Production database needs additional env vars: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

## Project Patterns

### File Uploads
- Centralized file upload handling in `utils/file_uploads.py`
- Files encrypted using timestamp-based SHA256 hashing
- Example usage:
  ```python
  from utils.file_uploads import encrypted_filename
  
  class YourModel(models.Model):
      file = models.FileField(
          upload_to=lambda instance, filename: encrypted_filename(
              instance, filename, 'your-base-folder'
          )
      )
  ```

### Localization
- Brazilian Portuguese (`pt-br`) as default language
- São Paulo timezone (`America/Sao_Paulo`)
- UTF-8 encoding enforced project-wide

### Static & Media Files
- Static files served from `static/` directory, collected to `staticfiles/`
- User uploads stored in `media/` directory
- File paths resolved relative to `BASE_DIR`

## Development Workflow

1. **Environment Setup**:
   ```cmd
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database**:
   ```cmd
   python manage.py migrate
   ```

3. **Run Development Server**:
   ```cmd
   python manage.py runserver
   ```

## Key Dependencies

- `django-environ`: Environment variable management
- `pillow`: Image processing for file uploads
- See `requirements.txt` for complete list with versions

## Common Tasks

### Adding New Apps
1. Create app in `apps/` directory:
   ```cmd
   python manage.py startapp your_app apps/your_app
   ```
2. Add to `INSTALLED_APPS` in `config/settings.py`

### Database Operations
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`