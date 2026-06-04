import pandas as pd

from supabase_db import SupabaseError, excel_row_to_student, is_fake_student, upsert_students

EXCEL_FILE = '2024-28_STUDENTS.xlsx'
BATCH_SIZE = 250


def main():
    df = pd.read_excel(EXCEL_FILE, header=1)
    rows = []

    for record in df.to_dict(orient='records'):
        if is_fake_student(record):
            continue
        student = excel_row_to_student(record, clear_payments=True)
        if student['registration_no'] and student['student_name']:
            rows.append(student)

    for start in range(0, len(rows), BATCH_SIZE):
        try:
            upsert_students(rows[start:start + BATCH_SIZE])
        except SupabaseError as exc:
            print("Import failed.")
            print("Run supabase_schema.sql in your Supabase SQL Editor first, then run this script again.")
            raise exc
        print(f"Imported {min(start + BATCH_SIZE, len(rows))}/{len(rows)} students")

    print(f"Done. Imported {len(rows)} students with past payment fields cleared.")


if __name__ == '__main__':
    main()
