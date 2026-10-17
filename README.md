# OrganLink: National Organ Transplant Registry

OrganLink is a web-based organ matching and transplant management registry built with **Flask** and **MySQL**. Many countries lack a centralized waitlist, which leads to organs being misallocated, wasted, or traded illegally. OrganLink gives hospitals, patients, donors, and administrators a single transparent, database-driven platform with fair organ allocation based on medical urgency and biological compatibility.

> Course project for Database Systems, FAST-NUCES (Section BCS-4A).

## Features

- **User registration and authentication:** secure, role-based login for each type of user.
- **Patient and donor profiling:** medical history, blood group, and tissue type records.
- **Waitlist queue management:** patients are automatically prioritized by medical urgency and wait time.
- **Organ matching:** SQL queries find compatible donor-recipient pairs by blood group and organ type.
- **Transaction-safe allocation:** ACID-compliant transactions lock an organ record when it is assigned, so it cannot be double-booked.
- **Audit logging:** every status update and match is recorded for regulatory review.

## User Roles

| Role | What they can do |
|------|------------------|
| **System Admin** | View system-wide statistics and audit logs, monitor suspicious activity, and approve hospitals. |
| **Hospital Coordinator** | Register patients and donors, update patient urgency, and view available matches for their hospital's patients. |
| **Patient** | Create a profile, view their waiting-list status, and update contact information. |
| **Donor** | Register willingness to donate, specify which organs they offer, and update health status. |

## Tech Stack

- **Front end:** HTML5, CSS3, JavaScript
- **Back end:** Python (Flask)
- **Database:** MySQL (designed up to BCNF)

## Database Highlights

- Schema normalized up to **BCNF**.
- Advanced SQL: joins, aggregate queries, and compatibility matching.
- Allocation runs inside a transaction using row-level locking (`SELECT ... FOR UPDATE`) to guarantee an organ is assigned to only one patient.
- Status changes and matches are written to an audit log table.

## Getting Started

### Prerequisites

- Python 3.9+
- MySQL 8.0+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/fazeeltariq/Organ_Donation_System.git
   cd Organ_Donation_System
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   mysql -u root -p -e "CREATE DATABASE organlink;"
   mysql -u root -p organlink < database/schema.sql
   mysql -u root -p organlink < database/sample_data.sql
   ```

5. **Configure database credentials** in your config file or environment variables (host, user, password, database name).

6. **Run the application**
   ```bash
   python app.py
   ```
   Then open `http://127.0.0.1:5000` in your browser.

## Project Structure

```
Organ_Donation_System/
├── app.py              # Flask application entry point
├── database/
│   ├── schema.sql      # Table definitions
│   └── sample_data.sql # Demo data
├── templates/          # HTML templates
├── static/             # CSS and JavaScript
├── requirements.txt
└── README.md
```

## Scope

**In scope:** web interface for user and hospital management, BCNF database design, advanced SQL queries and secure transaction handling for allocation, and matching by blood group and organ type.

**Out of scope:** real-time tracking of organ transport, financial or insurance processing, and integration with third-party hospital software.

## Assumptions

- Hospitals provide accurate and truthful medical data.
- Users have a stable internet connection.
- The system is populated with sample data for demonstration.

## Team

- Mubashir Sikandar (24K-1038)
- Fazeel Tariq (24K-0919)
- Muhammad Hizbullah (24K-1001)
