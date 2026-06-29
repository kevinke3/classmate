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

### Finance Portal (Upgraded)
- `/finance-portal` requires `finance` or `admin` role (others redirected to `/login`)
- **10 sidebar sections**: Dashboard, Fee Structures, Student Accounts, Payments, Invoices, Receipts, Expenses, Reports, Notifications, Settings
- **Dashboard section**: 4 KPI cards (collected today/week/month/year), 4 summary cards (expected revenue, outstanding, net income, pending invoices), 3 Chart.js charts (revenue trend line, outstanding by class bar, payment methods doughnut), recent transactions list
- **Section navigation**: SPA-style via `data-section` attributes on nav items; `switchSection()` toggles `.content-section.active` class and updates `#pageTitle`/`#pageSubtitle`
- **Record Payment**: header button `#btnQuickPayment` opens modal with student dropdown, amount, method (cash/bank_transfer/cheque/mobile_money), reference. Submitting auto-creates a Receipt and triggers print dialog with A5 school-branded document
- **Fee Structures**: CRUD table with name, class, year, term, total amount, components. Seeded with 4 structures (Tuition Fee Form 1-4)
- **Student Accounts**: Card grid with search. Click "View Profile" to see detailed financial modal (total invoiced/paid/outstanding, payments table, invoices table with status badges, action buttons)
- **Reports**: 4 report cards (Collection, Arrears, Fully Paid, Student Statement). Arrears report shows student table with outstanding amounts and export button
- **Settings**: General settings form (currency, prefixes, penalty rate, grace period, reminders, footer text), fee categories list (10 seeded with mandatory/optional badges), bank accounts section
- **Sidebar isolation**: finance role only sees Finance nav items; sidebar collapse CSS class toggles but may not visually collapse (known issue)
- **Login tip**: The login form may have autocomplete issues with computer-use tools. Using `browser_console` to call the login API directly and set `localStorage.token` is more reliable, then navigate to `/finance-portal`
- **Dashboard API**: `GET /api/finance/dashboard` returns KPIs, monthly_revenue (6 months), outstanding_by_class, payment_methods, recent_transactions (last 10). Values update in real-time after payments
- **Finance Settings API**: `GET/PUT /api/finance/settings` for currency, prefixes, grace period, etc. `GET /api/finance/fee-categories` for categories. `GET /api/finance/bank-accounts` for bank accounts

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
- **Invoice status refresh**: After recording a payment, the Invoices tab may not refresh to show updated invoice status/balance. The backend correctly updates invoices, but the frontend `loadInvoices()` might not be re-called. Dashboard KPIs do update correctly. Verify via API if in doubt.
- **Sidebar collapse on Finance Portal**: The `.collapsed` class is toggled on the sidebar element, but the CSS width transition may not apply on the finance portal template (stays at 260px). The collapse works on other portals (teacher, admin).
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

# Get finance dashboard (upgraded)
curl -s http://localhost:5000/api/finance/dashboard \
  -H "Authorization: Bearer $FIN_TOKEN"

# Get finance stats (legacy)
curl -s http://localhost:5000/api/finance/stats \
  -H "Authorization: Bearer $FIN_TOKEN"

# Get invoices
curl -s http://localhost:5000/api/finance/invoices \
  -H "Authorization: Bearer $FIN_TOKEN"

# Get fee categories
curl -s http://localhost:5000/api/finance/fee-categories \
  -H "Authorization: Bearer $FIN_TOKEN"

# Get finance settings
curl -s http://localhost:5000/api/finance/settings \
  -H "Authorization: Bearer $FIN_TOKEN"

# Get arrears report
curl -s http://localhost:5000/api/finance/reports/arrears \
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
