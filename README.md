# Tuition Management System

A production-quality private tuition management application built with Python and Streamlit.

---

## Origin

My mother has been teaching private tuition classes for years. She handles everything herself : the scheduling, the lesson planning, tracking which topics she covered with which student, remembering test scores across months, and writing progress updates for parents. For a long time she did all of this across a combination of paper registers, WhatsApp messages, and memory.

But she faced problems like, she would lose track of whether a student had attended a session two weeks ago. She could not quickly answer a parent who asked how their child had been performing over the past three months. Writing individual progress notes for every student at the end of each month took her an entire weekend. And because everything lived in different places, there was no single view of how a student was actually doing over time.

She asked me if I could build something that would let her track the details of each student properly, visualise their progress so she could spot trends herself, and generate clean monthly reports she could send directly to parents. Reports that a parent could read and immediately understand, without needing any context beyond what was on the page.

This application is the result of that conversation.

---

## What It Does

The system covers the full lifecycle of managing a private tuition practice.

**Student management** : Every student has a profile that stores their grade, subject, parent contact details, join date, and how many classes they are expected to attend per month. Students can be added, edited, and deactivated without losing their historical data.

**Recurring schedules** : The teacher defines which days of the week each student attends and at what time. These weekly slots are stored as schedule entries and serve as the basis for automatic session generation.

**Automatic session generation** : Instead of creating individual class entries by hand, the teacher selects a student and a month and the system generates every session for that month from the schedule. Sessions that already exist are skipped, so the operation is safe to run multiple times. There is also a bulk mode that generates sessions for all active students at once.

**Lesson logging** : Each generated session starts empty. The teacher fills in the topic taught, any homework assigned, and her remarks after each class. The dashboard surfaces sessions that are past their date but have not been logged yet, so nothing slips through.

**Test recording and analytics** : Tests are logged against a student with a name, topic, date, total marks, and marks scored. The system computes percentages and letter grades automatically. Analytics across all tests for a student show the average score, highest and lowest scores, and whether performance is improving, declining, or stable based on the most recent tests.

**Monthly PDF reports** : For any student and any month, the system generates a complete PDF report. The report includes the student and parent details, an at-a-glance summary of attendance and test scores, a full lesson log table showing every topic covered, test results with colour-coded grades, a performance summary paragraph, overall trend statistics, and a free-form teacher comments section. The PDF is formatted to be readable by a parent with no technical background and no prior context about the system.

**Dashboard** : The home screen shows today's scheduled classes, upcoming classes in the next seven days, recent test scores across all students, a grade distribution chart, and alerts for any past sessions that have not been logged.

---

## Technology Stack

| Layer | Technology |
|---|---|
| User interface | Streamlit |
| Database | SQLite |
| ORM | SQLAlchemy |
| Data processing | Pandas |
| PDF generation | ReportLab |
| Charts | Plotly |
| Language | Python 3.10+ |

SQLite was chosen deliberately. This application runs on a single machine used by a single teacher. There is no need for a network database server, no configuration overhead, and no ongoing maintenance. The entire database is a single file that can be backed up by copying it.

---

## Project Structure

```
tuition_manager/
|
|-- app.py                        Entry point. Streamlit page config, sidebar
|                                 navigation, and page routing.
|
|-- database/
|   |-- models.py                 SQLAlchemy ORM models: Student, Schedule,
|   |                             ClassSession, Test.
|   |-- db.py                     Engine setup, SessionLocal factory, db_session
|                                 context manager, and init_db().
|
|-- services/
|   |-- student_service.py        CRUD operations for students.
|   |-- schedule_service.py       CRUD operations for weekly schedule slots.
|   |-- session_service.py        Session CRUD, automatic monthly generation,
|   |                             attendance statistics.
|   |-- lesson_service.py         Lesson logging (topic, homework, remarks)
|   |                             and unlogged session detection.
|   |-- test_service.py           Test CRUD, analytics, Pandas DataFrame export.
|   |-- report_service.py         Report payload assembly and PDF file management.
|
|-- ui/
|   |-- dashboard.py              Home screen with KPIs, class lists, alerts.
|   |-- students_page.py          Student list, add form, edit and deactivate.
|   |-- schedule_page.py          Schedule slot management, bulk session generation.
|   |-- sessions_page.py          Session viewer, lesson log form, manual sessions.
|   |-- tests_page.py             Test entry, records table, performance charts.
|   |-- reports_page.py           PDF generation, data preview, report history.
|
|-- utils/
|   |-- report_utils.py           ReportLab PDF builder. All layout, colour, and
|                                 table construction for generated reports.
|
|-- data/
|   |-- tuition.db                SQLite database file. Created on first run.
|
|-- reports/                      Generated PDF reports are stored here.
```

The architecture separates concerns strictly. The `ui/` layer only calls `services/`. The `services/` layer only calls `database/` and `utils/`. No UI code touches the database directly, and no database code contains business logic.

---

## Data Models

### Student

| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key, auto-increment |
| name | String | Required |
| class_grade | String | e.g. "Grade 10", "Class 8" |
| subject | String | e.g. "Mathematics" |
| parent_name | String | Optional |
| parent_phone | String | Optional |
| parent_email | String | Optional |
| join_date | Date | Defaults to today |
| monthly_class_count | Integer | Default 8 |
| is_active | Boolean | Deactivation preserves history |

### Schedule

| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| student_id | Integer | Foreign key to Student |
| day_of_week | Integer | 0 = Monday, 6 = Sunday |
| start_time | Time | |
| end_time | Time | |

### ClassSession

| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| student_id | Integer | Foreign key to Student |
| session_date | Date | |
| start_time | Time | Copied from schedule on generation |
| end_time | Time | Copied from schedule on generation |
| topic_taught | Text | Filled in by teacher after class |
| homework | Text | Optional |
| remarks | Text | Optional |
| is_attended | Boolean | Default True |
| is_generated | Boolean | True if auto-generated, False if manual |

### Test

| Field | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| student_id | Integer | Foreign key to Student |
| date | Date | |
| test_name | String | e.g. "Unit Test 1" |
| topic | String | e.g. "Quadratic Equations" |
| total_marks | Float | |
| marks_scored | Float | |
| comments | Text | Optional |

Percentage and letter grade are computed as properties on the model and are never stored, they are always derived from `marks_scored` and `total_marks` so they stay consistent if either value is corrected.

---

## Installation

### Requirements

- Python 3.10 or later
- pip

### Steps

Clone the repository and navigate into it.

```bash
git clone https://github.com/your-username/tuition-manager.git
cd tuition-manager
```

Create and activate a virtual environment.

```bash
python3 -m venv venv
source venv/bin/activate          # Linux / macOS
venv\Scripts\activate             # Windows
```

Install dependencies.

```bash
pip install streamlit sqlalchemy pandas reportlab plotly
```

Run the application.

```bash
streamlit run app.py
```

The browser will open automatically at `http://localhost:8501`. On the first run, the application creates the `data/` directory and initialises `tuition.db` with all required tables. No database configuration is needed.

---

## Running the Application

Two launcher scripts are provided, one for Linux and macOS (`run.sh`) and one for Windows (`run.bat`). Both do the same work in the same order. After the first run, subsequent launches skip the setup steps that are already complete and start in a few seconds.

### Linux and macOS

```bash
chmod +x run.sh
./run.sh
```

### Windows

Double-click `run.bat`, or run it from a terminal:

```
run.bat
```

### What the scripts do

Both scripts perform the following steps before starting the application.

**Check Python** : Verifies that Python 3.10 or later is installed and available. If Python is missing or the version is too old, the script exits immediately with a message explaining what to install and where to get it, rather than failing later with a cryptic import error.

**Create the virtual environment** : Creates a `venv/` directory in the project root using the system Python. If `venv/` already exists the step is skipped entirely.

**Upgrade pip** : Ensures the package installer inside the virtual environment is current. A stale pip can cause package installs to fail silently on newer Python versions.

**Install missing packages** : Checks each required package individually by attempting to import it. Only the packages that are not already installed are downloaded. On the first run this installs streamlit, sqlalchemy, pandas, reportlab, and plotly. On every subsequent run this step completes in under a second.

**Create required directories** : Creates the `data/` and `reports/` directories if they do not exist. The application writes the SQLite database into `data/` and saves generated PDF reports into `reports/`. Without these directories the application would error on first launch.

**Start the application** : Launches Streamlit using the virtual environment's own executable and opens the application at `http://localhost:8501`. Press `Ctrl+C` in the terminal window to stop the server.

### Prerequisites

The only thing that needs to be installed manually before using the launcher scripts is Python 3.10 or later.

On Linux and macOS, Python is typically available through the system package manager:

```bash
# Ubuntu / Debian
sudo apt install python3 python3-venv

# Arch / Arch-based distros
sudo pacman -Syu python python-pip python-virtualenv

# macOS with Homebrew
brew install python
```

On Windows, download the installer from `https://www.python.org/downloads/` and make sure to check the option that says "Add Python to PATH" during installation. Without that option the launcher script will not be able to find Python.

Everything else, like the virtual environment, all Python packages, and the required directories, is handled automatically by the launcher.

---

## Usage Guide

The recommended workflow for a new setup follows this order.

**1. Add students**

Go to the Students page and use the Add Student tab. Fill in the student's name, grade, and subject at minimum. Parent contact details are optional but appear on generated PDF reports.

**2. Define schedules**

Go to the Schedules page and add the weekly time slots for each student. A student who attends on Monday and Thursday at 4 PM would get two schedule entries. These slots drive automatic session generation.

**3. Generate monthly sessions**

Still on the Schedules page, use the Generate Monthly Sessions tab. Select a student (or choose all students), pick the month and year, and click Generate. The system will create a ClassSession entry for every matching weekday in that month.

**4. Log lessons after each class**

Go to the Sessions page. The Log Lesson tab shows sessions that have not been logged yet. Select a session, fill in the topic, homework, and any remarks, and save.

**5. Record test results**

Go to the Tests page and use the Log Test tab. Enter the test name, topic, date, and marks. The percentage and grade are computed automatically.

**6. Generate a monthly report**

Go to the Reports page. Select the student, month, and year. Optionally type teacher comments that will appear at the bottom of the PDF. Click Generate. The report downloads directly from the browser and is also saved to the `reports/` folder for later access.

---

## PDF Report Structure

Each generated report contains the following sections in order.

**Header** : Report title and the month and year the report covers.

**Student information** : Name, grade, subject, parent name, phone, and email.

**At a glance** : Five summary statistics: total sessions held, sessions attended, attendance percentage, number of tests taken, and average test score for the month.

**Topics covered** : A table of every attended session with the date, topic taught, homework assigned, and teacher remarks.

**Test performance** : A table of every test in the month with the date, name, topic, marks scored, total marks, percentage, and grade. Percentages are colour-coded: green for 75 and above, amber for 50 to 74, red below 50. Any per-test comments appear beneath the table.

**Performance summary** : Overall trend (Improving, Declining, or Stable), all-time average, highest and lowest scores on record, and the current month's average.

**Teacher's comments** : The free-form text entered at report generation time.

**Footer** : Generation date and a confidentiality note.

Report files follow the naming convention `StudentName_Month_Year_Report.pdf`, for example `Rahul_March_2026_Report.pdf`.

---

## Architecture Notes

**Session management** : All database sessions use either the `db_session()` context manager (for writes) or `get_db()` with a `finally: db.close()` block (for reads). Sessions are never left open. `expire_on_commit=False` is set on `SessionLocal` so that ORM objects returned from write operations remain accessible after the session closes.

**Eager loading** : All relationships that are accessed outside the session scope use `lazy="joined"` in the model definition. This means SQLAlchemy fetches related objects in the same SQL query rather than issuing a second query on attribute access, which would fail after the session is closed. This applies to `ClassSession.student`, `Test.student`, and `Schedule.student`.

**No raw SQL** : Every database operation goes through SQLAlchemy ORM queries. This keeps the code consistent and makes it straightforward to switch the underlying database engine if needed.

**Streamlit state** : Page navigation is handled through `st.session_state.page`. No `st.Page` or multi-file Streamlit routing is used, which keeps the entry point simple and the import structure explicit.

---

## Backup

The entire application state lives in two places.

- `data/tuition.db` : All student records, schedules, sessions, and test data.
- `reports/` : All generated PDF reports.

Back up both of these. The simplest approach is to copy them to a cloud storage folder or an external drive on a schedule. The database file can be copied while the application is not running.

---

## Known Limitations

- Single-user only. There is no authentication and no concept of multiple teacher accounts.
- No image or file attachments. Lesson logs are text only.
- PDF reports require all session and test data to already be entered. The system does not send reports automatically.
- The application does not send emails or notifications. Reports must be downloaded and shared manually.

---

## License

MIT License. See `LICENSE` for details.

---

## Acknowledgements

Built for my mother, who has been teaching for a loooong time.