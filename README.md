# Paragon Apartment Management System (PAMS)

A web-based apartment management system built with Django for Paragon, a multi-location property company operating across Bristol, Cardiff, London, and Manchester.

## My Role
**Backend Developer** — responsible for database models, business logic, URL routing, and form handling.

## My Contributions
- Designed and implemented all database models (models.py)
- Built backend views and business logic for all 6 user roles
- Implemented URL routing and Django form classes
- Integrated role-based access control throughout the application

## Project Info

- **Module:** UFCF7S-30-2 — Systems Development Group Project
- **University:** University of the West of England, Bristol
- **Academic Year:** 2025–26
- **Team:**
  - Bertun Alpaydin (24004914) — Frontend
  - Arda Pekar (24061895) — Backend

## Tech Stack

- **Backend:** Python 3.12, Django 5.x
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, Chart.js
- **Database:** SQLite
- **Deployment:** UWE CSCTCloud

## Features

- Role-based access control (6 roles: Tenant, Frontdesk, Finance, Maintenance, Admin, Manager)
- Tenant dashboard with payment history, maintenance requests, complaints and Chart.js visualisations
- Admin dashboard with tenant payment charts and late payment bar chart
- Finance panel with collected vs pending rent reports
- Maintenance staff panel with cost, time and scheduled date tracking
- Manager panel with city-level occupancy statistics and city expansion
- Reports page with occupancy and financial summaries
- Early lease termination with 1 month notice and 5% penalty calculation

## Installation
```bash
git clone https://github.com/Dlyrock/SDGP02526-24061895.git
cd SDGP02526-24061895
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install django
python manage.py migrate
python manage.py runserver
```

Open `http://127.0.0.1:8000` in your browser.

## Create Admin User
```bash
python manage.py createsuperuser
```

Then go to `http://127.0.0.1:8000/admin` to manage users and assign roles.

## Project Structure
```
pams/
├── core/
│   ├── models.py        # Database models
│   ├── views.py         # Business logic
│   ├── urls.py          # URL routing
│   ├── forms.py         # Form classes
│   └── templates/       # HTML templates
│       ├── admin/       # Staff panel templates
│       └── tenant/      # Tenant dashboard templates
├── pams/
│   ├── settings.py      # Django settings
│   └── urls.py          # Root URL config
└── manage.py
```

## User Roles

| Role | Access |
|------|--------|
| TENANT | Dashboard, payments, maintenance, complaints, early termination |
| FRONTDESK | Tenant registration and search |
| FINANCE | Payment reports, late payment overview |
| MAINTENANCE | Status updates, cost and time logging |
| ADMIN | Full access to all panels and reports |
| MANAGER | City-level reports and city expansion |
