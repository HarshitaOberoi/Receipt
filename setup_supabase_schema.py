"""Create the students table and RLS policies in Supabase."""

import argparse
import getpass
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import psycopg2

from supabase_db import SUPABASE_URL

SCHEMA_FILE = Path(__file__).with_name('supabase_schema.sql')


def project_ref_from_url(url):
    host = urlparse(url).netloc
    match = re.match(r'^([^.]+)\.supabase\.co$', host)
    if not match:
        raise SystemExit(f'Could not parse Supabase project ref from SUPABASE_URL: {url}')
    return match.group(1)


def db_connection(password, db_url=None, project_ref=None):
    if db_url:
        return psycopg2.connect(db_url)

    project_ref = project_ref or project_ref_from_url(SUPABASE_URL)
    return psycopg2.connect(
        host=f'db.{project_ref}.supabase.co',
        port=5432,
        dbname='postgres',
        user='postgres',
        password=password,
        sslmode='require',
        connect_timeout=20,
    )


def run_schema(connection):
    sql = SCHEMA_FILE.read_text(encoding='utf-8')
    connection.autocommit = True
    with connection.cursor() as cursor:
        cursor.execute(sql)
    connection.autocommit = False


def main():
    parser = argparse.ArgumentParser(description='Create the Supabase students table.')
    parser.add_argument(
        '--db-url',
        default=os.getenv('SUPABASE_DB_URL'),
        help='Full PostgreSQL URL. Defaults to SUPABASE_DB_URL.',
    )
    parser.add_argument(
        '--password',
        default=os.getenv('SUPABASE_DB_PASSWORD'),
        help='Database password. Defaults to SUPABASE_DB_PASSWORD.',
    )
    args = parser.parse_args()

    password = args.password
    if not args.db_url and not password:
        password = getpass.getpass('Supabase database password: ').strip()

    if not args.db_url and not password:
        print('Missing database credentials.')
        print('Set SUPABASE_DB_PASSWORD or SUPABASE_DB_URL, or pass --password.')
        print('Find the password in Supabase Dashboard -> Project Settings -> Database.')
        return 1

    if not SCHEMA_FILE.exists():
        print(f'Schema file not found: {SCHEMA_FILE}')
        return 1

    try:
        connection = db_connection(password, db_url=args.db_url)
    except psycopg2.Error as exc:
        print(f'Could not connect to Supabase Postgres: {exc}')
        return 1

    try:
        run_schema(connection)
    except psycopg2.Error as exc:
        print(f'Failed to apply schema: {exc}')
        return 1
    finally:
        connection.close()

    print('Supabase schema applied successfully.')
    print('Next: python import_excel_to_supabase.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
