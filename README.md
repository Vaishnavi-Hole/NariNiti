# Nariniti

**Empowering Women Entrepreneurs Across India**

A full-stack web platform connecting women entrepreneurs with business ideas, government schemes, and mentors.

- **Developer / Owner**: Vaishnavi Hole
- **Frontend**: Next.js 14 (App Router) · TypeScript · Tailwind CSS · Lucide React
- **Backend**: Python · Django 4.2 · Django REST Framework · SimpleJWT
- **Database**: SQLite (development) — swap to PostgreSQL for production
- **Auth**: JWT via HttpOnly cookies

---

## Architecture

```
Browser
  │
  ▼
Next.js App Router  (localhost:3000)
  ├── Pages: /, /login, /register, /dashboard, /profile …
  ├── middleware.ts            ← cookie-based route guard
  └── /app/api/auth/*          ← server-side proxy routes
           │  (forwards cookies + body to Django)
           ▼
Django REST Framework  (localhost:8000)
  ├── POST  /api/auth/register/
  ├── POST  /api/auth/login/      → issues HttpOnly JWT cookies
  ├── POST  /api/auth/logout/     → blacklists refresh token, clears cookies
  ├── POST  /api/auth/refresh/    → rotates refresh token
  ├── GET   /api/auth/me/         → validates access_token cookie
  └── GET   /api/profile/         → protected user profile
       │
       └── SQLite db.sqlite3
```

### Authentication Flow

```
Register ──► Login ──► JWT issued ──► HttpOnly cookies set
                                           │
                         Page reload ──► /api/auth/me (validates cookie)
                                           │
                       Access expired ──► /api/auth/refresh (rotates tokens)
                                           │
                      Refresh invalid ──► Clear cookies ──► Redirect /login
                                           │
                             Logout ──► Blacklist refresh ──► Clear cookies
```

---

## Project Structure

```
nariniti/
├── backend/                   Django backend
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── nariniti/              Django project settings
│   │   ├── settings.py
│   │   └── urls.py
│   ├── authentication/        Auth app
│   │   ├── models.py          UserProfile model
│   │   ├── serializers.py     Registration / Login / Profile serializers
│   │   ├── views.py           Register, Login, Logout, Refresh, CurrentUser
│   │   ├── urls.py
│   │   ├── permissions.py     CookieJWTAuthentication
│   │   └── tests.py
│   └── profile_api/           Profile REST endpoints
│       ├── views.py
│       └── urls.py
│
└── frontend/                  Next.js frontend
    ├── middleware.ts           Route protection
    ├── app/
    │   ├── layout.tsx          Root layout with AuthProvider
    │   ├── page.tsx            Landing page
    │   ├── login/page.tsx      Login page
    │   ├── register/page.tsx   Registration page
    │   ├── dashboard/page.tsx  Protected dashboard
    │   └── api/auth/           Server-side proxy routes
    │       ├── login/route.ts
    │       ├── register/route.ts
    │       ├── logout/route.ts
    │       ├── refresh/route.ts
    │       └── me/route.ts
    ├── context/AuthContext.tsx Global auth state
    ├── hooks/useAuth.ts        Auth hook
    ├── lib/
    │   ├── api.ts              API client
    │   └── auth.ts             Auth functions
    └── components/
        ├── Navbar.tsx
        ├── auth/AuthGuard.tsx
        └── ui/
            ├── LoadingSpinner.tsx
            └── PasswordStrength.tsx
```

---

## Prerequisites

- **Python** 3.10+ (3.12 recommended)
- **Node.js** 18+ (24 recommended)
- **npm** 9+

---

## Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Copy environment file and fill in values
cp .env.example .env
```

Edit `.env`:

```
DJANGO_SECRET_KEY=your-long-random-secret-key
JWT_SIGNING_KEY=another-long-random-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
FRONTEND_URL=http://localhost:3000
```

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# (Optional) Create a superuser for Django admin
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

The backend will be available at **http://localhost:8000**.

---

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
```

Edit `.env.local`:

```
BACKEND_API_URL=http://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:3000
```

```bash
# Start the development server
npm run dev
```

The frontend will be available at **http://localhost:3000**.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django secret key (keep secret!) | — |
| `JWT_SIGNING_KEY` | JWT signing key (keep secret!) | fallback to SECRET_KEY |
| `DEBUG` | Enable debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `FRONTEND_URL` | Frontend base URL | `http://localhost:3000` |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `BACKEND_API_URL` | Django backend URL (server-side only) |
| `NEXT_PUBLIC_API_URL` | Next.js public API URL (client-safe) |

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register/` | Register a new user |
| `POST` | `/api/auth/login/` | Login (returns HttpOnly cookies) |
| `POST` | `/api/auth/logout/` | Logout (blacklists refresh token) |
| `POST` | `/api/auth/refresh/` | Refresh access token |
| `GET`  | `/api/auth/me/` | Get current authenticated user |

### Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/profile/` | Get user profile (protected) |
| `PUT`  | `/api/profile/` | Update user profile (protected) |

### Registration Request Body

```json
{
  "first_name": "Priya",
  "last_name": "Deshpande",
  "phone": "9876543210",
  "email": "priya@example.com",
  "password": "Secure@123",
  "confirm_password": "Secure@123",
  "preferred_language": "mr",
  "state": "MH",
  "accept_terms": true,
  "receive_updates": false
}
```

### Login Request Body

```json
{
  "identifier": "9876543210",
  "password": "Secure@123"
}
```

---

## Running Tests

### Backend

```bash
cd backend
python manage.py test authentication profile_api --verbosity=2
```

Tests cover:
- ✅ Valid registration
- ✅ Login by phone
- ✅ Login by email
- ✅ Invalid credentials (401)
- ✅ Logout (cookie clearing)
- ✅ Unauthenticated /me endpoint
- ✅ Profile GET and PUT

### Frontend

```bash
cd frontend
npm run build    # type-check and build
```

---

## Security Notes

- **Passwords** are hashed with Django's PBKDF2-SHA256 (never stored or logged in plain text)
- **JWT access tokens** live for 15 minutes; stored in HttpOnly cookies
- **JWT refresh tokens** live for 7 days; HttpOnly cookies, path-restricted to `/api/auth/refresh/`
- **Refresh token rotation** enabled — old token is blacklisted on each refresh
- **CORS** is configured to allow only the frontend origin
- **No secrets** are hard-coded — all loaded from environment variables
- In **production**, set `DEBUG=False`, `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`

---

## Production Checklist

- [ ] Set strong `DJANGO_SECRET_KEY` and `JWT_SIGNING_KEY`
- [ ] Set `DEBUG=False`
- [ ] Switch `DATABASES` to PostgreSQL
- [ ] Set `SECURE_SSL_REDIRECT=True`
- [ ] Set `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`
- [ ] Set `SECURE_HSTS_SECONDS` appropriately
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Serve with Gunicorn + Nginx (or similar)
- [ ] Use a process manager (systemd, supervisor)

---

*Built by Vaishnavi Hole · © 2024 Nariniti*
