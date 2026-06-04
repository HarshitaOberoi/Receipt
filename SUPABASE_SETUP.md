# Supabase Setup

1. Open your Supabase project.
2. Copy the database password from **Project Settings -> Database**.
3. Run:

```powershell
$env:SUPABASE_DB_PASSWORD="your-database-password"
python setup_supabase_schema.py
python import_excel_to_supabase.py
```

Alternatively, open **SQL Editor** and run the contents of `supabase_schema.sql`, then run the import command above.

The importer skips the local fake/test student and clears all existing payment fields while uploading the Excel student records.

The Flask app now reads dashboard, search, details, reports, and payment updates from Supabase.
