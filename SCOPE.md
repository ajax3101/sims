# Project scope

## Purpose

SIMS keeps student records and related academic and financial information for a higher education institution. Staff use the register to find students, review their records, maintain reference data, and prepare reports for office use.

## Data model

The database covers:

- academic years, education levels, specialties, educational programmes, study forms, and organizational units;
- study groups, staff, curator assignments, and their history;
- student profiles, group memberships, status history, and documents;
- semesters, disciplines, curricula, grades, and academic debts;
- contracts, payment schedules, and payments;
- import batches and row-level import issues.

Specialties support the 2015 numeric and 2024 letter classifiers. Group course is derived from the admission year, entry course, and selected academic year. Academic debts follow final and retake grades. Tuition debt is calculated from due instalments and recorded payments.

## Application functions

- Student register with server-side search, sorting, pagination, and filters.
- Student card with general information, study history, grades, debts, contracts, and payments.
- Management screens for specialties, groups, staff, and curator assignments.
- DOCX and XLSX student-roster import with validation, duplicate handling, and a row-level report.
- Academic-debt and tuition-debt reports, plus an individual student card, exported as XLSX, DOCX, or PDF.

## Current limits

- XLSX imports for debt and contract registers are not implemented. The importer currently accepts student rosters only.
- Authentication and roles are not implemented.
- The repository does not contain real grade, debt, or contract records. Synthetic records must be clearly identified as demo data.
- Source rosters contain personal data. Keep them local; `input_data/` is excluded from Git.

## Technology

- Backend: Python 3.14+, FastAPI, SQLAlchemy async, Alembic, PostgreSQL.
- Frontend: React, TypeScript, Vite, Tailwind CSS, and shadcn/ui components.
- Document processing: `python-docx` and `openpyxl`.
- Report export: XLSX, DOCX, and PDF.
