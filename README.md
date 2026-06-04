# Student Fee Management

Flask web app for managing student records, fee payments, and financial reports. Data is stored in Supabase.

## Requirements

- Python 3.10+
- A Supabase project with the `students` table created

## Quick start

### 1. Install dependencies

```powershell
cd d:\students
pip install -r requirements.txt
```

### 2. Set up Supabase (first time only)

If the database is not set up yet:

1. Open your Supabase project.
2. Go to **SQL Editor** and run the contents of `supabase_schema.sql`.
3. Import student data from Excel:

```powershell
python import_excel_to_supabase.py
```

For more details, see [SUPABASE_SETUP.md](SUPABASE_SETUP.md).

### 3. Run the app

```powershell
python app.py
```

Open in your browser:

**http://127.0.0.1:5000**

Stop the server with `Ctrl+C`.

## Optional environment variables

Override Supabase settings if needed:

```powershell
$env:SUPABASE_URL="https://your-project.supabase.co"
$env:SUPABASE_KEY="your-publishable-key"
python app.py
```

To create the database schema from the terminal instead of the SQL Editor:

```powershell
$env:SUPABASE_DB_PASSWORD="your-database-password"
python setup_supabase_schema.py
```

## Project scripts

| Command | Purpose |
|---------|---------|
| `python app.py` | Start the web app |
| `python import_excel_to_supabase.py` | Import students from `2024-28_STUDENTS.xlsx` |
| `python setup_supabase_schema.py` | Create the Supabase table and policies |

## App features

- **Dashboard** — collection totals and recent payments
- **Students** — search by name, father name, or registration number
- **Reports** — export summaries as PDF or Excel
- **Settings** — institution profile and backup download
