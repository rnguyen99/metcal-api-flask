# Metcal Asset API

Flask-based asset management API with JWT authentication, designed for Windows IIS + Waitress hosting.

## Features
- JWT bearer authentication with bcrypt-hashed users.
- CRUD endpoints for assets backed by SQLite.
- Centralized logging (console + `logs/api.log`).
- Request/response middleware with correlation details.
- CORS enabled for all `/api/*` routes.

## Getting Started

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python init_db.py  # seeds admin user + sample assets
python main.py  # or waitress-serve main:app
```

The initializer seeds a default admin user (`admin` / `password`). Change it immediately in production.

### Requesting a Token

```http
POST /api/token
Content-Type: application/json

{ "username": "admin", "password": "password" }
```

Response:
```json
{ "access_token": "...", "token_type": "bearer", "expires_in": 86400 }
```

Include `Authorization: Bearer <token>` for every protected asset request.

### Asset Endpoints
- `GET /api/assets`
- `GET /api/asset/<id>`
- `POST /api/asset`
- `PUT /api/asset/<id>`

See `models.py` for request schema details.

## IIS Deployment
1. Ensure Python, `waitress`, and project dependencies are installed on the server.
2. Set an environment variable `PYTHON_PATH` pointing to the Python executable (e.g., `C:\Python311\python.exe`).
3. Place the project under the IIS site root and copy `web.config` as provided.
4. Grant the IIS App Pool identity write access to the `logs` directory.
5. Restart the site; IIS will launch Waitress via the HTTP Platform handler.

## Logging
- Default location: `logs/api.log` (rotating 5 MB × 5 files).
- Request logs capture method, path, response status, IP, authenticated user, and latency.
- Unhandled exceptions produce stack traces for troubleshooting.
