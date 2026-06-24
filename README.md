# ClassMate

A modern school management platform built as a premium SaaS product. Designed with clean, futuristic aesthetics inspired by platforms like Linear, Stripe, and Notion.

## Features

- **Role-Based Access Control** - 5 roles: Admin, Teacher, Student, Parent, and Finance Officer -- each with a dedicated portal and permissions
- **Student Management** - Admissions, records, academic tracking
- **Teacher Management** - Faculty profiles, class assignments, workload
- **Academics** - Classes, subjects, timetables, assignments
- **Finance Officer Portal** - Dedicated high-security portal for recording payments, generating invoices, printing receipts, and tracking student balances
- **School Settings** - Admin can configure school name, logo, motto, address, email, academic year, and term -- branding flows into all printed documents
- **Printable Invoices & Receipts** - Professional school-branded documents with signature lines, ready for printing and distribution
- **Attendance** - Daily tracking, reports, trend analysis
- **Examinations** - Exam creation, grading, report cards, rankings
- **Messaging** - Real-time communication via Flask-SocketIO
- **Notifications** - Assignment deadlines, fee reminders, attendance alerts
- **Document Management** - Secure file storage with permission-based access
- **Analytics** - Performance charts, revenue trends, attendance overview

## Tech Stack

- **Backend**: Flask 3.0, SQLAlchemy 2.0, Flask-JWT-Extended, Flask-SocketIO
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (vanilla, separate files)
- **Charts**: Chart.js 4.4
- **Icons**: Lucide Icons
- **Font**: Outfit (Google Fonts)

## Design System

- Clean white background with black typography
- Red accent color (#E63946)
- Glassmorphism effects, smooth animations
- Responsive design (Desktop, Tablet, Mobile)
- Collapsible sidebar navigation
- Modern card-based layouts

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/kevinke3/classmate.git
cd classmate

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Create database
createdb classmate

# Run the application (creates tables automatically)
python run.py

# Seed sample data (optional but recommended)
python -m backend.seed
```

### Running

```bash
python run.py
```

The application will be available at `http://localhost:5000`

### Default Credentials (after seeding)

| Role    | Email                          | Password   | Portal              |
|---------|--------------------------------|------------|---------------------|
| Admin   | admin@classmate.io             | admin123   | /dashboard          |
| Teacher | mary@classmate.io              | teacher123 | /teacher-portal     |
| Student | grace@student.classmate.io     | student123 | /student-portal     |
| Parent  | parent@classmate.io            | parent123  | /parent-portal      |
| Finance | finance@classmate.io           | finance123 | /finance-portal     |

## Roles & Permissions

### Admin (Headteacher/Principal)
- Full access to all modules and portals
- Configure school settings: name, logo, motto, email, address, academic year, term
- Manage students, teachers, classes, and all operations
- Access finance overview and analytics

### Finance Officer
- Dedicated `/finance-portal` with isolated sidebar (Finance + Settings only)
- Record fee payments (auto-generates receipts)
- Create and manage invoices
- View and print school-branded invoices and receipts
- Track student balances and outstanding fees
- All finance write operations protected with role-based access control

### Teacher
- Manage assigned classes and subjects
- Take attendance, create assignments
- Grade examinations and view student performance
- Communicate with parents and students

### Student
- View grades, assignments, timetables, and attendance
- Access announcements and exam schedules
- View fee balance and payment history

### Parent
- Monitor child's attendance and academic performance
- View fee balances and payment receipts
- Communicate with teachers

## Project Structure

```
classmate/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory
│   │   ├── models.py            # SQLAlchemy models (20+ models)
│   │   ├── main.py              # Page routes
│   │   ├── auth/                # JWT authentication, registration, password reset
│   │   ├── users/               # User management
│   │   ├── students/            # Student CRUD
│   │   ├── teachers/            # Teacher CRUD
│   │   ├── academics/           # Classes, subjects, timetables
│   │   ├── attendance/          # Attendance tracking
│   │   ├── finance/             # Payments, invoices, receipts (role-gated)
│   │   ├── examinations/        # Exams and grading
│   │   ├── messaging/           # Real-time messaging (SocketIO)
│   │   ├── notifications/       # Notification system
│   │   ├── analytics/           # Dashboard analytics
│   │   ├── settings/            # User + school settings
│   │   └── documents/           # Document management
│   ├── config.py                # Configuration
│   └── seed.py                  # Sample data (users, students, invoices, receipts)
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   ├── design-system.css
│   │   │   ├── components/      # Sidebar, header, cards, modal, tables
│   │   │   └── pages/           # Page-specific styles
│   │   └── js/
│   │       ├── utils/           # API client, auth manager
│   │       ├── components/      # Sidebar, notifications
│   │       └── pages/           # Page-specific logic
│   └── templates/
│       ├── base.html            # Layout template
│       ├── auth/                # Login, Register
│       ├── dashboard/           # Main dashboard
│       ├── students/            # Student management
│       ├── teachers/            # Teacher management
│       ├── academics/           # Academic management
│       ├── finance/             # Finance portal (invoices, receipts, payments)
│       ├── attendance/          # Attendance tracking
│       ├── messages/            # Messaging
│       ├── settings/            # User + school settings
│       ├── admin/               # Admin portal
│       ├── parent/              # Parent portal
│       ├── student/             # Student portal
│       └── teacher/             # Teacher portal
├── requirements.txt
├── run.py
├── .env.example
└── README.md
```

## API Endpoints

All API routes are prefixed with `/api/`:

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT)
- `GET /api/auth/me` - Current user profile
- `POST /api/auth/reset-password` - Password reset

### Students & Teachers
- `GET /api/students/` - List students
- `POST /api/students/` - Create student
- `GET /api/teachers/` - List teachers

### Finance (requires `admin` or `finance` role)
- `GET /api/finance/stats` - Financial overview (totals, counts)
- `GET /api/finance/payments` - List payments
- `POST /api/finance/payments` - Record payment (auto-creates receipt, applies to invoices)
- `GET /api/finance/invoices` - List invoices (filterable by status)
- `POST /api/finance/invoices` - Create invoice
- `GET /api/finance/invoices/<id>` - Get invoice with school branding
- `GET /api/finance/receipts` - List receipts
- `GET /api/finance/receipts/<id>` - Get receipt with school branding
- `GET /api/finance/student-balance/<id>` - Student balance summary

### School Settings (admin only)
- `GET /api/settings/school` - Get school configuration
- `PUT /api/settings/school` - Update school name, logo, motto, address, etc.

### Other
- `POST /api/attendance/mark` - Mark attendance
- `GET /api/examinations/` - List examinations
- `POST /api/messaging/messages` - Send message
- `GET /api/analytics/overview` - Dashboard analytics

## License

MIT
