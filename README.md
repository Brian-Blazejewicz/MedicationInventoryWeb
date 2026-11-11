# Medication Inventory Management System

A full-stack medication inventory management application built with **React, TypeScript, Python FastAPI, and PostgreSQL**.

The application manages medication records, tracks inventory quantities, records stock adjustments, and displays inventory transaction history. It is a separate web-based expansion of an existing Python/SQLite desktop project.

> **Development project:** This application is intended for learning and demonstration. It is not approved for production pharmacy operations or storage of sensitive patient information.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Database migrations | Alembic |
| Frontend testing | Vitest, React Testing Library |
| Backend testing | Pytest |
| Version control | Git and GitHub |

## Features

### Medication Management

- Create, view, edit, and delete medication records.
- Search and sort medication records.

### Inventory Management

- Add inventory using **Stock IN**.
- Remove inventory using **Stock OUT**.
- Validate inventory quantities and prevent withdrawals that exceed available stock.
- Record inventory adjustments in a transaction history.

### Transaction History

- Record inventory additions and removals.
- Display transaction quantities and timestamps.
- Retrieve transactions through REST API endpoints.

## Application Architecture

The application follows a client-server architecture:

1. **React + TypeScript** provides the interface and sends HTTP requests.
2. **FastAPI** implements REST endpoints, validates requests, and processes inventory operations.
3. **SQLAlchemy** interacts with **PostgreSQL** for persistent storage.
4. **Alembic** manages database schema migrations.

For local development, the React frontend runs at `http://localhost:5173` and the FastAPI backend at `http://127.0.0.1:8000`.

## Automated Testing

The following test counts were verified during development:

| Test suite | Passing tests |
| --- | ---: |
| Frontend | 30 |
| Backend | 31 |
| **Total** | **61** |

Frontend tests cover UI components, medication interactions, inventory operations, and transaction history. Backend tests cover API behavior, database operations, inventory transactions, and PostgreSQL integration.

## Local Development Setup (Windows 11)

### Prerequisites

Install:

- Python 3.11
- Node.js and npm
- PostgreSQL 18
- Git
- Visual Studio Code (recommended)

### 1. Clone the Repository

Open PowerShell:

```powershell
git clone https://github.com/Brian-Blazejewicz/MedicationInventoryWeb.git
cd MedicationInventoryWeb
```

### 2. Configure the Python Backend

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Using the virtual environment's Python executable directly avoids needing to change PowerShell's script execution policy.

### 3. Configure PostgreSQL

Using PostgreSQL or pgAdmin, create a development database named `medication_inventory` and an application role named `medication_app`. Assign a password to the role and grant it the permissions needed to connect to the database and run migrations in the application's schema.

From the `backend` directory, create your local configuration file:

```powershell
Copy-Item .env.example .env
```

Edit `backend/.env` with your local credentials:

```dotenv
DB_USER=medication_app
DB_PASSWORD=replace_with_your_actual_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=medication_inventory
```

**Never commit `.env` or real database credentials.** The `.env.example` file contains placeholders and is safe to commit.

> The exact PostgreSQL role creation and permission-grant commands are not yet documented or verified for a fresh installation.

### 4. Apply Database Migrations

From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

The project includes migrations for the medication and inventory transaction tables.

### 5. Start the FastAPI Backend

From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

Keep this terminal open.

### 6. Start the React Frontend

Open a second PowerShell terminal. From the project root:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open http://localhost:5173 in your browser. The frontend communicates with the FastAPI backend through HTTP requests.

### 7. Run Automated Tests

**Frontend:** From the `frontend` directory:

```powershell
npm.cmd test
npm.cmd run build
npm.cmd run lint
```

**Backend:** From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The backend integration tests require the dedicated PostgreSQL test database described below. Do not run them against a database containing data you need to preserve.

### PostgreSQL Integration Test Database

The integration tests use a dedicated database named `medication_inventory_test`, separate from the development database `medication_inventory`.

The tests reuse the database username, password, host, and port from `backend/.env`, but the test helper explicitly targets `medication_inventory_test`. It checks the intended database name before connecting and verifies the connected database name afterward.

Before running the integration tests:

1. Create the PostgreSQL database `medication_inventory_test`.
2. Grant the application role the required database and schema permissions.
3. Apply the project's Alembic migrations to the **test database** using a separately verified configuration or procedure.
4. Run the backend test suite from the `backend` directory.

The integration tests create fictional medication records and contain cleanup logic to remove the records and inventory transactions they create. Cleanup is best-effort and may not finish if a test process is forcibly interrupted.

**Do not store real inventory or patient data in the test database.** The exact migration procedure for this separate database is a remaining documentation task; the standard Alembic command above uses the development database configured in `backend/.env`.

### 8. Stop the Development Servers

Press `Ctrl + C` in each terminal running FastAPI or Vite.

## Security Notes

- PostgreSQL credentials are loaded from environment variables.
- `.env` files are excluded from version control; `.env.example` contains placeholder settings.
- The backend validates inventory transactions and rejects withdrawals that exceed available inventory.
- Authentication and authorization are **not yet implemented** and are planned for future development.
- This application is intended for local development and demonstration, not production pharmacy operations.

## Development Status

Implemented and tested: core medication management, stock adjustments, transaction history, frontend components, API operations, and PostgreSQL integration.

Planned work includes authentication, deployment, further automated testing, and more complete installation documentation.

## Project Background

This project expands on an earlier Python and SQLite desktop medication inventory system. The original desktop application is maintained separately.

The web version demonstrates full-stack application architecture, REST API development, relational database integration, automated testing, and version control practices.

## Author

Brian Blazejewicz
Computer Science Student — Southern New Hampshire University

- [LinkedIn](https://www.linkedin.com/in/brian-blazejewicz-8a38a1445/)
- [GitHub](https://github.com/Brian-Blazejewicz)
