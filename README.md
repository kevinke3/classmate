# ClassMate

A modern school management platform built as a premium SaaS product. Designed with clean, futuristic aesthetics inspired by platforms like Linear, Stripe, and Notion.

## Features

- **Role-Based Access Control** - Separate dashboards for Admin, Teacher, Student, and Parent
- **Student Management** - Admissions, records, academic tracking
- **Teacher Management** - Faculty profiles, class assignments, workload
- **Academics** - Classes, subjects, timetables, assignments
- **Finance** - Fee invoicing, M-Pesa integration, payment tracking, receipts
- **Attendance** - Daily tracking, reports, trend analysis
- **Examinations** - Exam creation, grading, report cards, rankings
- **Messaging** - Real-time communication via Flask-SocketIO
- **Notifications** - Assignment deadlines, fee reminders, attendance alerts
- **Document Management** - Secure file storage with permission-based access
- **Analytics** - Performance charts, revenue trends, attendance overview

## Tech Stack

- **Backend**: Flask, SQLAlchemy, Flask-JWT-Extended, Flask-SocketIO
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Charts**: Chart.js
- **Icons**: Lucide Icons
- **Font**: Outfit (Google Fonts)
- **Payments**: M-Pesa STK Push (Safaricom)

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
- PostgreSQL
- pip

### Installation

```bash
# Clone the repository
git clone <repo-url>
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

# Seed sample data (optional)
python -m backend.seed
```

### Running

```bash
python run.py
```

The application will be available at `http://localhost:5000`

### Default Credentials (after seeding)

| Role    | Email                          | Password   |
|---------|--------------------------------|------------|
| Admin   | admin@classmate.io             | admin123   |
| Teacher | mary@classmate.io              | teacher123 |
| Student | grace@student.classmate.io     | student123 |
| Parent  | parent@classmate.io            | parent123  |

## Project Structure

```
classmate/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # App factory
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── main.py              # Page routes
│   │   ├── auth/                # Authentication
│   │   ├── users/               # User management
│   │   ├── students/            # Student CRUD
│   │   ├── teachers/            # Teacher CRUD
│   │   ├── academics/           # Classes, subjects, timetables
│   │   ├── attendance/          # Attendance tracking
│   │   ├── finance/             # Fees, payments, M-Pesa
│   │   ├── examinations/        # Exams and grading
│   │   ├── messaging/           # Real-time messaging
│   │   ├── notifications/       # Notifications system
│   │   ├── analytics/           # Dashboard analytics
│   │   ├── settings/            # User settings
│   │   └── documents/           # Document management
│   ├── config.py                # Configuration
│   └── seed.py                  # Sample data
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
│       ├── finance/             # Finance management
│       ├── attendance/          # Attendance tracking
│       ├── messages/            # Messaging
│       ├── settings/            # User settings
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

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login (returns JWT)
- `GET /api/auth/me` - Current user profile
- `GET /api/students/` - List students
- `POST /api/students/` - Create student
- `GET /api/teachers/` - List teachers
- `POST /api/attendance/mark` - Mark attendance
- `GET /api/finance/payments` - List payments
- `POST /api/finance/mpesa/stk-push` - Initiate M-Pesa payment
- `GET /api/examinations/` - List examinations
- `POST /api/messaging/messages` - Send message
- `GET /api/analytics/overview` - Dashboard analytics

## License

MIT
