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

## Deploy on Vercel

This app uses Flask with zero-config support on Vercel. Your `app.py` is detected automatically.

### Before you deploy

1. Complete [Supabase setup](#2-set-up-supabase-first-time-only) so the `students` table exists and has data.
2. Push the project to GitHub (or GitLab/Bitbucket).

### Deploy with the Vercel dashboard

1. Go to [vercel.com/new](https://vercel.com/new) and import your repository.
2. Leave the framework preset as **Flask** (auto-detected).
3. Add these **Environment Variables** in project settings:

| Name | Value |
|------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Your Supabase publishable/anon key |
| `FLASK_SECRET_KEY` | A long random string for session security |

4. Click **Deploy**.

Your app will be live at `https://your-project.vercel.app`.

### Deploy with the Vercel CLI

```powershell
npm i -g vercel
cd d:\students
vercel
```

Follow the prompts. Set the same environment variables when asked, or add them later in the Vercel dashboard under **Settings → Environment Variables**.

To deploy to production:

```powershell
vercel --prod
```

### Vercel limitations

- **Settings saves** — changes on the Settings page are written to `settings.json`, which does not persist on Vercel’s serverless filesystem. Use the defaults in the repo, or move settings to Supabase later if you need editable production config.
- **Excel backup download** — the local `2024-28_STUDENTS.xlsx` file is not deployed. Use Supabase as the source of truth; export reports from the Reports page instead.
- **Import scripts** — run `import_excel_to_supabase.py` locally, not on Vercel.

Everything else (dashboard, search, payments, receipts, PDF/Excel reports) works through Supabase.

### Redeploy after changes

Push to your connected Git branch — Vercel redeploys automatically. Or run `vercel --prod` from the project folder.

