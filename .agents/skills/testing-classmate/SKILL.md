---
name: testing-classmate
description: Test the ClassMate school management platform end-to-end. Use when verifying UI, API, or auth changes.
---

# Testing ClassMate

## Prerequisites

- Python 3.12+
- PostgreSQL 14+

## Environment Setup

1. **Install PostgreSQL** (if not available):
   ```bash
   sudo apt-get install -y postgresql postgresql-client
   sudo pg_ctlcluster 14 main start
   ```

2. **Create database and user:**
   ```bash
   sudo -u postgres psql -c "CREATE USER classmate WITH PASSWORD 'classmate';"
   sudo -u postgres psql -c "CREATE DATABASE classmate OWNER classmate;"
   ```

3. **Install Python dependencies:**
   ```bash
   cd /home/ubuntu/repos/classmate
   pip install -r requirements.txt
   ```

4. **Start the Flask server** (eventlet must be monkey-patched before imports):
   ```bash
   python -c "
   import eventlet
   eventlet.monkey_patch()
   import os
   os.environ['DATABASE_URL'] = 'postgresql://classmate:classmate@localhost:5432/classmate'
   from backend.app import create_app, socketio, db
   app = create_app('development')
   with app.app_context():
       db.create_all()
   socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
   " > /tmp/flask.log 2>&1 &
   ```
   - **Do NOT use `python run.py`** with debug=True + eventlet. The reloader spawns child processes that may fail to bind the port. Use the inline script above with `debug=False, use_reloader=False`.
   - Wait ~3 seconds, then verify with: `curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login` (expect 200)

5. **Seed the database:**
   ```bash
   export DATABASE_URL="postgresql://classmate:classmate@localhost:5432/classmate"
   python -m backend.seed
   ```

## Default Login Credentials (after seeding)

| Role    | Email                         | Password   | Redirects to       |
|---------|-------------------------------|------------|--------------------|
| Admin   | admin@classmate.io            | admin123   | /dashboard         |
| Teacher | mary@classmate.io             | teacher123 | /teacher-portal    |
| Student | grace@student.classmate.io    | student123 | /student-portal    |
| Parent  | parent@classmate.io           | parent123  | /parent-portal     |

## Key Testing Flows

### Login Flow
- Navigate to `http://localhost:5000/login`
- Invalid credentials: submit wrong email/password, expect red alert "Invalid email or password"
- Valid credentials: submit admin creds, expect redirect to `/dashboard`
- JWT tokens stored in `localStorage` keys: `access_token`, `refresh_token`, `user`

### Dashboard
- `/dashboard` requires auth (redirects to `/login` if no token)
- 4 stat cards with animated counters (data-target attributes)
- 2 Chart.js canvases: `#attendanceChart` (line), `#revenueChart` (bar)
- Activity feed and Upcoming Events are static HTML
- API data from `GET /api/analytics/overview` updates counter targets

### Sidebar
- Toggle button `#sidebarToggle` adds `sidebar-collapsed` class to `<body>`
- Collapsed state: only icons visible, text labels hidden
- State persists in `localStorage` key `sidebar_collapsed`

### Students Page
- `/students` loads cards from `GET /api/students/?per_page=50`
- Search input `#searchInput` filters cards on `input` event by name/admission number
- Card/table view toggle via `#cardViewBtn` / `#tableViewBtn`
- "Add Student" button opens modal form

## Known Issues / Gotchas

- **eventlet + debug mode**: Running with `debug=True` causes the Flask reloader to spawn a child process. With eventlet, this may prevent port binding. Always use `debug=False, use_reloader=False` for testing.
- **Student class_name**: Student cards might show "Class: N/A" because the API response includes `class_id` (integer) but the frontend template expects `class_name` (string). This might be a display issue.
- **Notification panel**: Badge shows a count but panel content might use skeleton loaders. Real notifications require additional API integration.

## Devin Secrets Needed

None required for local testing. All credentials are hardcoded in the seed script.

## API Verification (curl)

```bash
# Login
curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@classmate.io","password":"admin123"}'

# Get analytics (requires token)
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@classmate.io","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s http://localhost:5000/api/analytics/overview \
  -H "Authorization: Bearer $TOKEN"

# Get students
curl -s http://localhost:5000/api/students/ \
  -H "Authorization: Bearer $TOKEN"
```
