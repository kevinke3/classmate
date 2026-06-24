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
|---------|-------------------------------|------------|--------------------||
| Admin   | admin@classmate.io            | admin123   | /dashboard         |
| Teacher | mary@classmate.io             | teacher123 | /teacher-portal    |
| Parent  | parent@classmate.io           | parent123  | /parent-portal     |
| Finance | finance@classmate.io          | finance123 | /finance-portal    |

Note: Students do not have login accounts. Student data is accessed by parents through the Parent Portal.

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

### Parent Portal
- `/parent-portal` shows merged student + parent content: stat cards (attendance, average, fee balance, class rank), academic performance table, fee payment history, timetable, upcoming assignments, announcements
- Sidebar isolation: parent role only sees Parent Portal + Settings nav items (all other nav hidden)
- Parents access student academic data here instead of a separate student portal

### Students Page (Admin)
- `/students` loads cards from `GET /api/students/?per_page=50`
- Students are records (no login accounts) with `first_name`/`last_name` directly on the `Student` model
- Search input `#searchInput` filters cards on `input` event by name/admission number
- Card/table view toggle via `#cardViewBtn` / `#tableViewBtn`
- "Add Student" modal: no email field (students don't have accounts)

### Finance Portal
- `/finance-portal` requires `finance` or `admin` role (others redirected to `/login`)
- 4 stat cards: Total Collected, Outstanding Balance, Total Payments, Invoices Issued
- 4 tabs: Payments, Invoices, Receipts, Student Balances
- **Create Invoice**: button opens modal with student dropdown, amount, description, term, academic year, due date
- **Record Payment**: button opens modal; recording a payment auto-creates a Receipt and auto-applies to oldest unpaid invoices
- **Print**: Print buttons on invoices/receipts open a modal with school-branded document (name, motto, address from SchoolSettings)
- **Sidebar isolation**: finance role only sees Finance + Settings nav items; `/finance` href rewritten to `/finance-portal`

### School Settings (Admin only)
- `/settings` > "School" nav item (only visible for admin role)
- Form fields: school name, motto, logo URL, email, phone, address, website, academic year, current term
- Saves via `PUT /api/settings/school` (403 for non-admin)
- Changes propagate to printed invoices/receipts via `SchoolSettings` model

### Role-Based Access Control
- Finance write endpoints (`POST /api/finance/payments`, `POST /api/finance/invoices`) require `admin` or `finance` role
- Other roles get `{"error":"Finance access required"}` with HTTP 403
- School settings PUT requires `admin` role only

## Known Issues / Gotchas

- **eventlet + debug mode**: Running with `debug=True` causes the Flask reloader to spawn a child process. With eventlet, this may prevent port binding. Always use `debug=False, use_reloader=False` for testing.
- **Student class_name**: Student cards show "Class: N/A" because the API response includes `class_id` (integer) but the frontend template expects `class_name` (string). This is a display issue, not a data issue.
- **Notification panel**: Badge shows "3" but panel content uses skeleton loaders. Real notifications require additional API integration.
- **Invoice status refresh**: After recording a payment, the Invoices tab may not refresh to show updated invoice status/balance. The backend correctly updates invoices, but the frontend `loadInvoices()` might not be re-called. Stats cards do update correctly. Verify via API if in doubt.
- **Server restart needed**: Since `use_reloader=False`, code changes require killing (`pkill -f "socketio.run"`) and restarting the Flask server. Always verify with curl after restart.
- **Sidebar collapsed state**: Sidebar state persists in localStorage. If testing sidebar visibility for a role, you may need to clear `localStorage.sidebar_collapsed` or expand manually.

## Devin Secrets Needed

None required for local testing. All credentials are hardcoded in the seed script.

## API Verification (curl)

```bash
# Login as admin
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@classmate.io","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Login as finance officer
FIN_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"finance@classmate.io","password":"finance123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Get finance stats
curl -s http://localhost:5000/api/finance/stats \
  -H "Authorization: Bearer $FIN_TOKEN"

# Get invoices
curl -s http://localhost:5000/api/finance/invoices \
  -H "Authorization: Bearer $FIN_TOKEN"

# Verify role security (teacher should get 403)
TEACH_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mary@classmate.io","password":"teacher123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -w "\nHTTP:%{http_code}" http://localhost:5000/api/finance/payments \
  -H "Authorization: Bearer $TEACH_TOKEN"
# Expected: {"error":"Finance access required"} HTTP:403

# Get school settings
curl -s http://localhost:5000/api/settings/school \
  -H "Authorization: Bearer $TOKEN"
```
