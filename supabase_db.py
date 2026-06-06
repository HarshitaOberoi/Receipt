import math
import os
from datetime import datetime
from urllib.parse import quote

import requests

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://jymgqxpxftllerhudugf.supabase.co').rstrip('/')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'sb_publishable_wCsaXT7xQfNFJwi4H9FCGw_ABNxkqZ0')
STUDENTS_TABLE = 'students'


class SupabaseError(Exception):
    pass


def is_missing_students_table(error):
    message = str(error)
    return 'PGRST205' in message and 'students' in message


def missing_students_table_message():
    return (
        "Supabase table public.students does not exist yet. "
        "Run: python setup_supabase_schema.py "
        "(or paste supabase_schema.sql into the Supabase SQL Editor), "
        "then run: python import_excel_to_supabase.py"
    )


def _headers(extra=None):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    if extra:
        headers.update(extra)
    return headers


def _request(method, path, **kwargs):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    response = requests.request(method, url, headers=_headers(kwargs.pop('headers', None)), timeout=30, **kwargs)
    if response.status_code >= 400:
        error = SupabaseError(f"Supabase {response.status_code}: {response.text}")
        if is_missing_students_table(error):
            raise SupabaseError(missing_students_table_message()) from error
        raise error
    if response.text:
        return response.json()
    return None


def clean_value(value):
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).strip()
    if text.lower() in {'', 'nan', 'nat', 'none'}:
        return None
    return value


def clean_text(value):
    value = clean_value(value)
    if value is None:
        return None
    return str(value).strip()


def clean_number(value):
    value = clean_value(value)
    if value is None:
        return 0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def is_fake_student(record):
    username = clean_text(record.get('Username')) or clean_text(record.get('username')) or ''
    registration = clean_text(record.get('Registration No.')) or clean_text(record.get('registration_no')) or ''
    name = clean_text(record.get('Student Name')) or clean_text(record.get('student_name')) or ''
    return (
        username.upper().startswith('FAKE') or
        registration == '99999999999' or
        name.upper() == 'TEST STUDENT'
    )


def excel_row_to_student(record, clear_payments=True):
    online_amount = 0 if clear_payments else clean_number(record.get('ONLINE AMOUNT'))
    offline_amount = 0 if clear_payments else clean_number(record.get('OFFLINE AMOUNT'))
    mode = None if clear_payments else clean_text(record.get('MODE OF PAYMENT'))
    fee_type = None if clear_payments else clean_text(record.get('TYPE'))

    sr_no = clean_value(record.get('Sr.No.'))
    try:
        sr_no = int(sr_no) if sr_no is not None else None
    except (TypeError, ValueError):
        sr_no = None

    return {
        'sr_no': sr_no,
        'username': clean_text(record.get('Username')),
        'registration_no': clean_text(record.get('Registration No.')),
        'student_name': clean_text(record.get('Student Name')),
        'date_of_birth': clean_text(record.get('Date Of Birth')),
        'father_name': clean_text(record.get("Father's Name")),
        'mother_name': clean_text(record.get("Mother's Name")),
        'category': clean_text(record.get('Category')),
        'ews_status': clean_text(record.get('EWS Status')),
        'aadhar_no': clean_text(record.get('Aadhar No.')),
        'degree': clean_text(record.get('Degree')),
        'mode_of_payment': mode,
        'online_amount': online_amount,
        'offline_amount': offline_amount,
        'fee_type': fee_type,
        'updated_at': datetime.utcnow().isoformat()
    }


def student_to_template(record):
    return {
        'Sr.No.': record.get('sr_no'),
        'Username': record.get('username'),
        'Registration No.': record.get('registration_no'),
        'Student Name': record.get('student_name'),
        'Date Of Birth': record.get('date_of_birth'),
        "Father's Name": record.get('father_name'),
        "Mother's Name": record.get('mother_name'),
        'Category': record.get('category'),
        'EWS Status': record.get('ews_status') or 'NO',
        'Aadhar No.': record.get('aadhar_no'),
        'Degree': record.get('degree'),
        'MODE OF PAYMENT': record.get('mode_of_payment'),
        'ONLINE AMOUNT': float(record.get('online_amount') or 0),
        'OFFLINE AMOUNT': float(record.get('offline_amount') or 0),
        'TYPE': record.get('fee_type')
    }


def upsert_students(records):
    if not records:
        return []
    return _request(
        'POST',
        f"{STUDENTS_TABLE}?on_conflict=registration_no",
        json=records,
        headers={'Prefer': 'resolution=merge-duplicates,return=minimal'}
    )


def fetch_students(limit=2000):
    return _request(
        'GET',
        f"{STUDENTS_TABLE}?select=*&order=sr_no.asc.nullslast&limit={limit}"
    ) or []


def fetch_student(registration_no):
    registration_no = quote(str(registration_no), safe='')
    rows = _request(
        'GET',
        f"{STUDENTS_TABLE}?select=*&registration_no=eq.{registration_no}&limit=1"
    ) or []
    return rows[0] if rows else None


def search_students(query, limit=100):
    query = str(query or '').strip()
    if not query:
        return []
    pattern = quote(f"*{query}*", safe='')
    return _request(
        'GET',
        f"{STUDENTS_TABLE}?select=*&or=(student_name.ilike.{pattern},father_name.ilike.{pattern},registration_no.ilike.{pattern})&order=sr_no.asc.nullslast&limit={limit}"
    ) or []


def update_payment(registration_no, mode, amount, fee_type, ews_status, receipt_no, date):
    amount = clean_number(amount)
    
    # First, fetch existing data to append
    existing = fetch_student(registration_no)
    if not existing:
        return None
        
    existing_types = clean_text(existing.get('fee_type')) or ""
    existing_modes = clean_text(existing.get('mode_of_payment')) or ""
    existing_history = clean_text(existing.get('username')) or ""
    
    # We store multiple values separated by "|"
    new_types = f"{existing_types}|{fee_type}" if existing_types else fee_type
    new_modes = f"{existing_modes}|{mode}" if existing_modes else mode
    
    # Store full history in 'username' column: amount|mode|date|receipt_no|type
    new_record = f"{amount}|{mode}|{date}|{receipt_no}|{fee_type}"
    new_history = f"{existing_history}||{new_record}" if existing_history else new_record
    
    payload = {
        'mode_of_payment': new_modes,
        'online_amount': (existing.get('online_amount') or 0) + (amount if mode == 'ONLINE' else 0),
        'offline_amount': (existing.get('offline_amount') or 0) + (amount if mode != 'ONLINE' else 0),
        'fee_type': new_types,
        'ews_status': clean_text(ews_status) or 'NO',
        'username': new_history,
        'updated_at': datetime.utcnow().isoformat()
    }
    registration_no = quote(str(registration_no), safe='')
    rows = _request(
        'PATCH',
        f"{STUDENTS_TABLE}?registration_no=eq.{registration_no}",
        json=payload,
        headers={'Prefer': 'return=representation'}
    ) or []
    return rows[0] if rows else None
