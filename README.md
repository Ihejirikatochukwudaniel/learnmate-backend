# LearnMate Backend 🚀

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Supabase-1.0+-orange.svg)](https://supabase.com/)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

A modern, scalable backend API for LearnMate - a comprehensive Learning Management System (LMS) built with FastAPI and Supabase.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Setup](#setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- 🔐 **Authentication & Authorization** - JWT-based auth with Supabase integration
- 👥 **User Management** - Profiles, roles, and permissions
- 📚 **Course Management** - Classes, assignments, and content
- 📊 **Grade Management** - Assignment grading and progress tracking
- 📝 **Attendance Tracking** - Student attendance monitoring
- 📤 **Submission System** - Assignment submission and review
- 👨‍💼 **Admin Panel** - Administrative controls and user management
- 🔍 **Real-time Updates** - Live notifications and updates via Supabase

## 🛠 Tech Stack

- **Backend Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT with PyJWT
- **API Documentation**: Auto-generated Swagger UI
- **Environment Management**: python-dotenv
- **Data Validation**: Pydantic
- **ASGI Server**: Uvicorn

## 🏗 Architecture

```
LearnMate Backend
├── 📁 app/
│   ├── main.py                 # FastAPI app instance
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Settings & configuration
│   │   ├── security.py        # JWT & auth utilities
│   │   └── dependencies.py    # Shared dependencies
│   ├── db/                     # Database layer
│   │   ├── models.py          # Data models
│   │   └── supabase.py        # Supabase client
│   ├── modules/                # Feature modules
│   │   ├── auth/              # Authentication
│   │   ├── admin/             # Admin panel
│   │   ├── profiles/          # User profiles
│   │   ├── classes/           # Course management
│   │   ├── assignments/       # Assignment system
│   │   ├── submissions/       # Submission handling
│   │   ├── grades/            # Grading system
│   │   └── attendance/        # Attendance tracking
│   ├── schemas/               # Pydantic schemas
│   └── utils/                 # Utility functions
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Supabase account and project
- Git

### Clone the Repository

```bash
git clone https://github.com/your-username/learnmate-backend.git
cd learnmate-backend
```

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Docker Setup (Recommended)

If you prefer using Docker:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run separately
docker build -t learnmate-backend .
docker run -p 8000:8000 --env-file .env learnmate-backend
```

## ⚙️ Setup

### Environment Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Fill in your Supabase credentials in `.env`:
```env
SUPABASE_URL=your-supabase-project-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

### Database Setup

Ensure your Supabase project has the following tables:
- `users` - User accounts
- `profiles` - Extended user information
- `classes` - Course/class data
- `assignments` - Assignment definitions
- `submissions` - Student submissions
- `grades` - Grading records
- `attendance` - Attendance logs

## 🎯 Usage

### Development Server

Start the development server with auto-reload:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit `http://localhost:8000` to see the API documentation.

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## 📡 API Endpoints

### Authentication
- `GET /` - Health check
- `GET /auth/me` - Get current user info

### Admin (Admin users only)
- `GET /admin/users` - List all users

### Profiles
- User profile management endpoints

### Classes
- Course and class management

### Assignments
- Assignment creation and management

### Submissions
- Student submission handling

### Grades
- Grading and progress tracking

### Attendance
- Attendance recording and reporting

## 🔧 Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Linting

```bash
flake8 .
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**LearnMate Backend** - Built with ❤️ using FastAPI and Supabase