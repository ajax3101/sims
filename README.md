# SIMS

SIMS is a student register for the academic office of a Ukrainian higher education institution. It keeps student records, study groups, grades, academic debts, tuition contracts, and payments in one place.

The interface is in Ukrainian. The backend provides a REST API and exports reports as XLSX, DOCX, and PDF.

## Features

- Search, filter, sort, and paginate student records.
- View student details, study history, grades, debts, contracts, and payments.
- Manage specialties, groups, staff, and curator assignments.
- Import student rosters from DOCX and XLSX files with a row-level report.
- Export academic-debt and tuition-debt reports, and an individual student card.

## Stack

- Python 3.14 or newer, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- React, TypeScript, Vite, Tailwind CSS

## Local setup

Requirements: Python 3.14+, [uv](https://docs.astral.sh/uv/), Node.js, npm, and Docker Compose.

Copy the local database settings and install the backend dependencies:

```sh
cp .env.example .env
uv sync --locked
```

Start PostgreSQL and apply the migrations:

```sh
docker compose up -d postgres
uv run alembic upgrade head
```

Run the API from the repository root:

```sh
uv run uvicorn sims.main:app --app-dir src --reload --port 8000
```

In a second terminal, install and start the frontend:

```sh
cd frontend
npm ci
npm run dev
```

Vite serves the interface at `http://localhost:5173` and proxies `/api` requests to the backend on port 8000. The API documentation is available at `http://localhost:8000/docs`.

## Importing rosters

Keep source files in a local directory. The `input_data/` directory is excluded from Git because roster files contain personal data.

Import one file or all supported files directly inside a directory:

```sh
uv run sims import /path/to/rosters
```

The importer currently supports DOCX and XLSX student rosters. It does not walk nested directories.

## Tests

Run the backend tests with:

```sh
uv run pytest
```

The backend test suite resets the database named by `SIMS_TEST_DATABASE_URL`. Keep that URL pointed at the dedicated test database (`sims_test`).

Run the frontend checks from `frontend/`:

```sh
npm test
npm run typecheck
npm run build
```

## Development notes

- The sample database credentials in `.env.example` are for local development only.
- Authentication and roles have not been implemented. Do not expose this app to a public network without adding access control.
- Synthetic records are marked in the interface when `SIMS_DEMO=true`.
- Real student records and other private source documents must stay outside the public repository.
