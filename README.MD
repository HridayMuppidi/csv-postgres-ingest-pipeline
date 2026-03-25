# CSV to PostgreSQL Ingest Pipeline

A production-grade Python data pipeline that loads CSV data into a PostgreSQL database with full idempotent upsert logic. Built with Docker for easy setup and deployment.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
- [How to Run the Loader](#how-to-run-the-loader)
- [How to View the Database](#how-to-view-the-database)
- [How to Run Tests](#how-to-run-tests)
- [Business Key Rationale](#business-key-rationale)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

This utility reads California historical property/landmark records from a CSV file and loads them into a PostgreSQL database. It is **idempotent** — meaning you can run it multiple times without creating duplicates. On each run:

- **Inserts** records that don't exist yet
- **Updates** records that already exist
- Always sets `lastupdatedt` to the current timestamp and `updateuser` from `.env`

---

## Tech Stack

- **Python 3.13**
- **PostgreSQL 18** (via Docker)
- **Docker & Docker Compose**
- **psycopg2** — PostgreSQL driver
- **python-dotenv** — environment variable management
- **pytest** — unit testing
- **Adminer** — database UI

---

## Project Structure

```
csv-postgres-ingest-pipeline/
├── src/
│   ├── config.py          # loads environment variables
│   ├── db.py              # database connection and table creation
│   ├── loader.py          # CSV reading and upsert logic
│   └── logging_config.py  # logging setup
├── tests/
│   ├── test_loader.py     # unit tests
│   └── sample.csv         # sample test data
├── sql/
│   └── create_table.sql   # DDL script to create the table
├── data/                  # place your CSV files here
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

---

## Prerequisites

Before you begin, make sure you have the following installed:

1. **Docker Desktop** — [Download here](https://www.docker.com/products/docker-desktop/)
   - After installing, open Docker Desktop and make sure it is running (green status at the bottom left)
   - Docker Desktop must be running before any `docker compose` commands will work

2. **Git** — [Download here](https://git-scm.com/)

3. **Python 3.10+** — [Download here](https://www.python.org/downloads/)
   - Required only for running tests locally
   - Not needed for running the pipeline — Docker handles Python inside the container

---

## Before You Begin

All commands in this README should be run in your terminal:
- **Windows** — use **Command Prompt** or **PowerShell**
- **Mac/Linux** — use **Terminal**

Make sure you are always in the project root folder (`csv-postgres-ingest-pipeline/`) when running commands.


## Setup and Installation

### Step 1 — Clone the repository

```bash
git clone https://github.com/HridayMuppidi/csv-postgres-ingest-pipeline.git
cd csv-postgres-ingest-pipeline
```
>After cloning, all subsequent commands should be run from inside the `csv-postgres-ingest-pipeline/` folder.

### Step 2 — Local Environment Setup

> This step is only required for running tests locally. If you only want to run the pipeline using Docker, skip to [Create your .env file](#step-3----create-your-env-file).


```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

---


### Step 3 — Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ca_properties_db
DB_USER=postgres
DB_PASSWORD=your_password_here
LOG_LEVEL=INFO
UPDATE_USER=your_name
```

### Step 4 — Place your CSV file in the `data/` folder

Copy your CSV file into the `data/` folder of the project:

```
data/
└── your_file.csv
```

### Step 5 — Configure your CSV path

You have two options for specifying the CSV file:

**Option A — Set it in `.env` (runs automatically on `docker compose up`):**

Add this to your `.env` file:
```
CSV_PATH=data/your_file.csv
```

**Option B — Pass it via command line (more flexible, overrides `.env`):**

Leave `CSV_PATH` out of `.env` and pass the path when running. See [How to Run the Loader](#how-to-run-the-loader) for details.

### Step 6 — Start all containers

**Option A — Run in background (recommended):**
```bash
docker compose up --build -d
```
This runs everything silently in the background. View logs separately with:
```bash
docker compose logs csv_postgres_ingest_pipeline
```

**Option B — Run in foreground (see logs immediately):**
```bash
docker compose up --build
```
This shows all logs in real time in your terminal.

This starts:
- PostgreSQL database
- Python ingest application
- Adminer database UI

> **Important:** After the first run use `docker compose up -d` (without `--build`) for subsequent runs. Only use `--build` when you have made code changes.

---

## How to Run the Loader

### Using `.env` for CSV path

If you set `CSV_PATH` in your `.env` file, the loader runs automatically when you do `docker compose up`.

### Using command line for CSV path

To load a specific CSV file via command line:

```bash
docker compose run csv_postgres_ingest_pipeline python src/loader.py --csv data/your_file.csv
```

> **Note:** The command line argument always overrides the `CSV_PATH` value in `.env` if both are set.

### To load a different CSV file at any time

1. Copy your new CSV file into the `data/` folder
2. Run:
```bash
docker compose run csv_postgres_ingest_pipeline python src/loader.py --csv data/new_file.csv
```

### Viewing logs

If you ran with `-d` (background mode), view logs with:
```bash
docker compose logs csv_postgres_ingest_pipeline
```

Example output:
```
INFO - Starting CSV loader...
INFO - California Properties Table created successfully or already exists.
INFO - Reading CSV from data/Alpine.csv
INFO - Successfully read 139 rows from the CSV file.
INFO - Number of inserted records: 139
INFO - Number of updated records: 0
INFO - CSV to database loader executed successfully
```

### Enable debug logging

Set in `.env`:
```
LOG_LEVEL=DEBUG
```
This shows detailed logs for every record processed.

> **Note:** All timestamps are stored in UTC timezone.

---

## How to View the Database

Adminer is a lightweight database UI included in the Docker setup.

> **Important:** The Docker containers must be running to access Adminer. If you ran with `-d`, the containers stay running in the background and Adminer will be accessible. If you ran without `-d`, keep the terminal open. Once you close the containers, Adminer will no longer be accessible.

To check if containers are running:
```bash
docker compose ps
```

Once containers are running, open your browser and go to:

```
http://localhost:8080/?pgsql=postgres_database&username=postgres&db=ca_properties_db&ns=public&select=california_properties
```

Enter your database password (same as `DB_PASSWORD` in your `.env`) and you will see all records in the `california_properties` table directly.

---

## How to Run Tests

Make sure your local environment is set up (see [Local Environment Setup](#step-2--local-environment-setup)), then run:

```bash
pytest tests/ -v
```

Example output:
```
tests/test_loader.py::test_read_file_valid_csv PASSED
tests/test_loader.py::test_read_file_not_found PASSED
tests/test_loader.py::test_read_file_empty_csv PASSED
tests/test_loader.py::test_record_exists_returns_true PASSED
tests/test_loader.py::test_record_exists_returns_false PASSED
tests/test_loader.py::test_insert_record_success PASSED
tests/test_loader.py::test_insert_record_rollback_on_error PASSED
tests/test_loader.py::test_update_record_success PASSED
tests/test_loader.py::test_upsert_row_inserts_when_record_does_not_exist PASSED
tests/test_loader.py::test_upsert_row_updates_when_record_exists PASSED
tests/test_loader.py::test_upsert_row_duplicate_row PASSED
tests/test_loader.py::test_upsert_row_missing_otis_id PASSED
```

---

## Business Key Rationale

### Primary Key Choice: `OTIS ID`

`OTIS ID` was chosen as the primary key (business key) for the following reasons:

- **Always populated** — unlike `Primary Number` and `Property Number` which are frequently blank, `OTIS ID` is present in every record
- **System generated** — it appears to be a system-generated identifier, meaning it is designed to be unique per record
- **Stored as VARCHAR** — stored as `VARCHAR(50)` rather than `INTEGER` because identifiers should never be used for arithmetic, and future IDs may contain non-numeric characters or leading zeros

### Why not a composite key?

A composite key using multiple columns was considered but rejected because:
- Most candidate columns (`Primary Number`, `Property Number`, `Name`) contain null/blank values
- Demographic columns like `City`, `County`, `Name` are not reliable identifiers
- A composite key increases complexity in the upsert logic without adding reliability

### Column Type Decisions

- `VARCHAR(50)` — short controlled fields like `otis_id`, `zip_code`
- `VARCHAR(255)` — medium length fields like `name`, `parent_district`
- `TEXT` — unpredictable length fields like `evaluation_information`, `aliases_and_alias_types`, `associated_resources`
- `DATE` — `date_modified` and `export_date` (PostgreSQL auto-converts `MM/DD/YYYY` format)
- `TIMESTAMP` — `lastupdatedt` audit column stores date and time in UTC

---

## Troubleshooting

### Docker Desktop not running
**Error:** `Cannot connect to the Docker daemon`

**Fix:** Open Docker Desktop and wait for the engine to start (green status at bottom left), then retry.

---

### Database connection failed
**Error:** `could not translate host name "postgres_database"`

**Fix:** Make sure both services are on the same network. Check `docker-compose.yml` has `networks: app_network` on both services.

---

### CSV file not found
**Error:** `CSV file not found at path: data/your_file.csv`

**Fix:** Make sure your CSV file is placed inside the `data/` folder of the project before running.

---

### Data too long for column
**Error:** `Data too long for column. Consider increasing column size in create_table.sql`

**Fix:** Open `sql/create_table.sql` and change the affected column type from `VARCHAR(n)` to `TEXT`. Then run:
```bash
docker compose down -v
docker compose up --build -d
```

---

### Port already in use
**Error:** `Bind for 0.0.0.0:5432 failed: port is already allocated`

**Fix:** Another service is using port 5432. Stop it or change `DB_PORT` in `.env` and update `docker-compose.yml` accordingly.

---

### Tests failing due to import errors
**Error:** `ModuleNotFoundError: No module named 'loader'`

**Fix:** Make sure your virtual environment is activated and you're running pytest from the project root:
```bash
venv\Scripts\activate
pytest tests/ -v
```

---

### Adminer not accessible
**Error:** `localhost:8080` not loading in browser

**Fix:** Make sure your containers are still running:
```bash
docker compose ps
```
If they are stopped, restart them:
```bash
docker compose up -d
```