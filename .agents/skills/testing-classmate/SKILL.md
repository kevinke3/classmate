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

4. **Start the Flask server:**
   ```bash
   cd /home/ubuntu/repos/classmate
   export FLASK_APP=backend.app:create_app
   export DATABASE_URL="postgresql://classmate:classmate@localhost:5432/classmate"
   python3 -m flask run --host=0.0.0.0 --port=5000 > /tmp/flask.log 2>&1 &
   ```
   - Alternative (with eventlet/socketio): Use the inline script with `debug=False, use_reloader=False`
   - Wait ~3 seconds, then verify with: `curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/login` (expect 200)

5. **Seed the database:**
   ```bash
   export DATABASE_URL="postgresql://classmate:classmate@localhost:5432/classmate"
   python3 -m backend.seed
   ```

## Default Login Credentials (after seeding)

| Role              | Email                  | Password   | Redirects to              |
|-------------------|------------------------|------------|---------------------------|
| Admin             | admin@classmate.io     | admin123   | /dashboard                |
| Deputy            | john@classmate.io      | teacher123 | /deputy-portal            |
| Senior Teacher    | agnes@classmate.io     | teacher123 | /senior-teacher-portal    |
| Head of Studies   | peter@classmate.io     | teacher123 | /hos-portal               |
| Class Teacher     | mary@classmate.io      | teacher123 | /class-teacher-portal     |
| Parent            | parent@classmate.io    | parent123  | /parent-portal            |
| Finance           | finance@classmate.io   | finance123 | /finance-portal           |

Note: Students do not have login accounts. Student data is accessed by parents through the Parent Portal.

## Key Testing Flows

### Login Flow
- Navigate to `http://localhost:5000/login`
- Invalid credentials: submit wrong email/password, expect red alert "Invalid email or password"
- Valid credentials: submit admin creds, expect redirect to `/dashboard`
- JWT tokens stored in `localStorage` keys: `access_token`, `refresh_token`, `user`
- **Important**: Clear `localStorage` between logins to avoid stale token conflicts. The portal JS reads `localStorage.getItem('token') || localStorage.getItem('access_token')` — an old `token` key can override the fresh `access_token`.

### Deputy Headteacher Portal (`/deputy-portal`)
- **API prefix**: `/api/deputy`
- **Dashboard KPIs**: total_students, total_teachers, open_discipline, pending_leaves
- **Expected seed values**: Students=8, Teachers=5, Discipline Cases=3, Pending Leaves=2
- **Sidebar sections** (10): Dashboard, Student Management, Discipline, Staff Supervision, Class Allocation, Attendance, Leave Requests, Student Welfare, Duty Roster, Reports
- **Discipline table**: Shows 4 records (Misconduct, Insubordination, Fighting, Truancy)
- **Charts**: 2 Chart.js canvases (discipline doughnut + enrollment bar)
- **Sidebar collapse**: Toggle button adds `.collapsed` class, icons remain visible via `min-width` styling

### Senior Teacher Portal (`/senior-teacher-portal`)
- **API prefix**: `/api/senior-teacher`
- **Dashboard KPIs**: total_teachers, total_lessons, completion_rate, coverage
- **Expected seed values**: Teachers=5, Lessons=3, Completion=33.3%, Coverage=63.5%
- **Sidebar sections** (8): Dashboard, Lesson Plans, Schemes of Work, Observations, Syllabus Coverage, Announcements, Events, Reports
- **Lesson Plans table**: 3 rows (Introduction to Algebra, The Water Cycle, Parts of Speech)
- **Charts**: Lessons doughnut chart (completed vs planned segments)

### Head of Studies Portal (`/hos-portal`)
- **API prefix**: `/api/hos`
- **Dashboard KPIs**: total_students, overall_mean, pass_rate, active_interventions, total_subjects, syllabus_coverage
- **Expected seed values**: Students=8, Overall Mean=0, Pass Rate=0%, Active Interventions=1, Subjects=8, Syllabus Coverage=63.5%
- **Sidebar sections** (7): Dashboard, Examinations, Academic Reports, Curriculum, Interventions, Targets, Reports
- **Charts**: Class performance bar chart (Form 1-4), Subject performance radar/bar (8 subjects)
- **Interventions**: 1 record (Grace Wanjiku, Mathematics, Remedial Classes, target 35->50, active)
- **Note**: Performance charts may show 0 bars if no exam grade data exists — this is expected

### Class Teacher Portal (`/class-teacher-portal`)
- **API prefix**: `/api/class-teacher`
- **Dashboard KPIs**: student_count, attendance_rate, open_discipline, class_names
- **Expected seed values**: Students=2, Attendance=0% (before marking), Open Cases=1, Class="Form 1"
- **Additional dashboard info**: Homework Pending, Unpaid Fees, Present Today counter, Recent Behavior Records
- **Sidebar sections** (7): Dashboard, My Students, Attendance, Behavior, Counseling, Parent Messages, Reports
- **My Students**: 2 student cards (Grace Wanjiku, Lucy Akinyi) with "Profile" button
- **Student Profile modal**: Shows attendance %, fee status, discipline history, behavior records
- **Attendance CRUD**: Date picker + Load button → table with status dropdowns (Present/Absent/Late) + Remarks → "Save Attendance" → alert "N attendance records saved"
- **After save**: Dashboard "Today Attendance" and "Present Today" KPIs update live

### Finance Portal (`/finance-portal`)
- **API prefix**: `/api/finance`
- **Dashboard**: KPIs (collected today/week/month/year), 3 Chart.js charts (revenue trend, outstanding by class, payment methods), recent transactions
- **10 sidebar sections**: Dashboard, Fee Structures, Student Accounts, Payments, Invoices, Receipts, Expenses, Reports, Notifications, Settings
- **Record Payment**: Modal with student dropdown, amount, method → auto-generates Receipt with A5 school-branded print dialog
- **Reports**: Collection, Arrears, Fully Paid, Student Statement. Arrears report shows student table with outstanding amounts
- **Settings**: Currency, prefixes, penalty rate, grace period, fee categories (10 seeded), bank accounts

### Parent Portal (`/parent-portal`)
- Shows merged student + parent content: stat cards, academic performance, fee payment history, timetable, assignments, announcements
- Sidebar isolation: only Parent Portal + Settings visible

### School Settings (Admin only)
- `/settings` > "School" nav item
- Form: school name, motto, logo URL, email, phone, address, website
- Saves via `PUT /api/settings/school` (403 for non-admin)

### Cross-Portal Role Security
- Each portal's API enforces role checks via `@require_role()` decorator
- Class Teacher cannot access `/api/deputy/*` (returns 403 "Deputy or admin access required")
- Finance endpoints require `finance` or `admin` role
- School settings PUT requires `admin` role only

## Known Issues / Gotchas

- **localStorage token conflict**: Portal JS reads `token` before `access_token`. Always clear localStorage between role switches during testing. In real use, login flow handles this correctly.
- **eventlet + debug mode**: Running with `debug=True` causes reloader issues with eventlet. Use `debug=False, use_reloader=False` or plain `flask run`.
- **Student class_name**: Student cards show "Class: N/A" because API returns `class_id` (integer) but frontend expects `class_name` (string). Display issue, not data issue.
- **Invoice status refresh**: After recording a payment, the Invoices tab may not refresh to show updated status. Backend updates correctly; verify via API if needed.
- **Sidebar collapse on Finance Portal**: The `.collapsed` class toggles but CSS width transition may not apply (stays at 260px). Works on other portals.
- **HoS Performance chart empty**: Bar chart renders axis labels (Form 1-4) but no data bars when no exam grades exist in seed data. Expected behavior.
- **Server restart**: With `use_reloader=False`, code changes require killing and restarting the Flask server.

## Devin Secrets Needed

None required for local testing. All credentials are hardcoded in the seed script.

## API Verification (curl)

```bash
# Login as admin
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@classmate.io","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Login as deputy
DEPUTY_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@classmate.io","password":"teacher123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Login as class teacher
CT_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mary@classmate.io","password":"teacher123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Login as finance officer
FIN_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"finance@classmate.io","password":"finance123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Deputy dashboard
curl -s http://localhost:5000/api/deputy/dashboard \
  -H "Authorization: Bearer $DEPUTY_TOKEN"

# Senior Teacher dashboard
ST_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"agnes@classmate.io","password":"teacher123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:5000/api/senior-teacher/dashboard \
  -H "Authorization: Bearer $ST_TOKEN"

# HoS dashboard
HOS_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"peter@classmate.io","password":"teacher123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -s http://localhost:5000/api/hos/dashboard \
  -H "Authorization: Bearer $HOS_TOKEN"

# Class Teacher dashboard
curl -s http://localhost:5000/api/class-teacher/dashboard \
  -H "Authorization: Bearer $CT_TOKEN"

# Finance dashboard
curl -s http://localhost:5000/api/finance/dashboard \
  -H "Authorization: Bearer $FIN_TOKEN"

# Verify cross-portal role security (class teacher cannot access deputy)
curl -s -w "\nHTTP:%{http_code}" http://localhost:5000/api/deputy/dashboard \
  -H "Authorization: Bearer $CT_TOKEN"
# Expected: {"error":"Deputy or admin access required"} HTTP:403

# Get school settings
curl -s http://localhost:5000/api/settings/school \
  -H "Authorization: Bearer $TOKEN"
```
