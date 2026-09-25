# Portfolio Django REST API Backend

This is the Python + Django REST Framework backend for Omm Prasad Jena's portfolio website.

## 🚀 Features

- **Contact API (`/api/contact/`)**: Receives and validates portfolio contact messages, storing them in PostgreSQL/SQLite for Django Admin management.
- **AI Chat API (`/api/chat/`)**: Groq-powered AI chat server endpoint with server-side portfolio system prompt and secret protection.
- **Health Check (`/api/health/`)**: Simple health status endpoint for monitoring and deployment verification.
- **Django Admin**: Protected admin panel to manage, view, filter, and mark contact messages.

---

## 🛠️ Local Development Setup

### 1. Create & Activate Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

Create `.env` file in `backend/`:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

# Database (Leave blank to fallback to SQLite for local development, or supply PostgreSQL URL)
DATABASE_URL=postgresql://user:password@localhost:5432/portfolio_db

# Groq API Key (Server-side only)
GROQ_API_KEY=your_groq_api_key_here

# Security / Domain settings
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 4. Database Migrations

```bash
python manage.py makemigrations api
python manage.py migrate
```

### 5. Create Admin Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Local Server

```bash
python manage.py runserver
```

The Django API server will run at: `http://localhost:8000`

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health/` | Health check endpoint |
| `POST` | `/api/contact/` | Submit portfolio contact message |
| `POST` | `/api/chat/` | Send message to AI assistant |
| `GET` | `/admin/` | Django Admin Panel |

---

## 🚢 Production Deployment (e.g. Render / Railway / VPS)

### Build Command:
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

### Start Command:
```bash
gunicorn config.wsgi:application
```

### Required Production Environment Variables:
- `SECRET_KEY`: Strong random secret key
- `DEBUG`: `False`
- `DATABASE_URL`: Production PostgreSQL database URL
- `GROQ_API_KEY`: Your Groq API key
- `ALLOWED_HOSTS`: Your Render backend domain (e.g., `your-backend.onrender.com`)
- `CORS_ALLOWED_ORIGINS`: Your Vercel frontend URL (e.g., `https://your-portfolio.vercel.app`)
- `CSRF_TRUSTED_ORIGINS`: Your Vercel frontend URL
