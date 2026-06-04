from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import json
from datetime import datetime
from io import BytesIO

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from supabase_db import (
    SupabaseError,
    fetch_student,
    fetch_students,
    search_students,
    student_to_template,
    update_payment
)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'secret_key_for_flash_messages')

EXCEL_FILE = '2024-28_STUDENTS.xlsx'
SETTINGS_FILE = 'settings.json'

DEFAULT_SETTINGS = {
    'institution_name': 'Kodefort',
    'contact_email': 'admin@kodefort.edu',
    'contact_phone': '+91 98765 43210',
    'address': '123 Education Drive, Academic City, State - 560001',
    'backup_schedule': 'Daily'
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    with open(SETTINGS_FILE, 'r', encoding='utf-8') as settings_file:
        saved_settings = json.load(settings_file)

    settings = DEFAULT_SETTINGS.copy()
    settings.update(saved_settings)
    return settings

def save_settings(settings):
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as settings_file:
        json.dump(settings, settings_file, indent=2)

def template_students(records):
    return [student_to_template(record) for record in records]


def build_report_summaries(students):
    category_totals = {}
    degree_totals = {}
    for student in students:
        online = float(student['ONLINE AMOUNT'] or 0)
        offline = float(student['OFFLINE AMOUNT'] or 0)
        category = student['Category'] or 'Uncategorized'
        degree = student['Degree'] or 'Unassigned'

        category_totals.setdefault(category, {'Category': category, 'ONLINE AMOUNT': 0, 'OFFLINE AMOUNT': 0, 'Total': 0})
        degree_totals.setdefault(degree, {'Degree': degree, 'ONLINE AMOUNT': 0, 'OFFLINE AMOUNT': 0, 'Total': 0})

        category_totals[category]['ONLINE AMOUNT'] += online
        category_totals[category]['OFFLINE AMOUNT'] += offline
        category_totals[category]['Total'] += online + offline
        degree_totals[degree]['ONLINE AMOUNT'] += online
        degree_totals[degree]['OFFLINE AMOUNT'] += offline
        degree_totals[degree]['Total'] += online + offline

    return list(category_totals.values()), list(degree_totals.values())


def load_report_summaries():
    try:
        students = template_students(fetch_students())
    except SupabaseError as exc:
        flash(str(exc), 'danger')
        return None, None
    return build_report_summaries(students)


def report_timestamp():
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def format_currency(value):
    return f"Rs. {float(value or 0):,.0f}"


def build_report_pdf(category_summary, degree_summary):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph('Financial Reports', styles['Title']),
        Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']),
        Spacer(1, 18),
        Paragraph('By Category', styles['Heading2']),
        Spacer(1, 8),
    ]

    category_table = [['Category', 'Online', 'Offline', 'Total']]
    for item in category_summary:
        category_table.append([
            item['Category'],
            format_currency(item['ONLINE AMOUNT']),
            format_currency(item['OFFLINE AMOUNT']),
            format_currency(item['Total']),
        ])

    elements.append(_report_table(category_table))
    elements.extend([
        Spacer(1, 18),
        Paragraph('By Degree', styles['Heading2']),
        Spacer(1, 8),
    ])

    degree_table = [['Degree', 'Online', 'Offline', 'Total']]
    for item in degree_summary:
        degree_table.append([
            item['Degree'],
            format_currency(item['ONLINE AMOUNT']),
            format_currency(item['OFFLINE AMOUNT']),
            format_currency(item['Total']),
        ])

    elements.append(_report_table(degree_table))
    doc.build(elements)
    buffer.seek(0)
    return buffer


def _report_table(rows):
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    try:
        students = template_students(fetch_students())
    except SupabaseError as exc:
        flash(str(exc), 'danger')
        students = []

    total_students = len(students)
    online_total = sum(float(student['ONLINE AMOUNT'] or 0) for student in students)
    offline_total = sum(float(student['OFFLINE AMOUNT'] or 0) for student in students)
    total_collected = online_total + offline_total

    paid_students = [
        student for student in students
        if float(student['ONLINE AMOUNT'] or 0) > 0 or float(student['OFFLINE AMOUNT'] or 0) > 0
    ]
    pending_students = total_students - len(paid_students)
    recent_transactions = list(reversed(paid_students[-5:]))
    
    # Data for charts (e.g., Online vs Offline)
    chart_data = {
        'labels': ['Online', 'Offline'],
        'values': [float(online_total), float(offline_total)]
    }
    
    return render_template('dashboard.html', 
                           total_students=total_students,
                           total_collected=total_collected,
                           pending_students=pending_students,
                           recent_transactions=recent_transactions,
                           chart_data=chart_data)

@app.route('/reports')
def reports():
    category_summary, degree_summary = load_report_summaries()
    if category_summary is None:
        category_summary, degree_summary = [], []

    return render_template(
        'reports.html',
        category_summary=category_summary,
        degree_summary=degree_summary
    )


@app.route('/reports/export/excel')
def export_reports_excel():
    category_summary, degree_summary = load_report_summaries()
    if category_summary is None:
        return redirect(url_for('reports'))

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pd.DataFrame(category_summary).to_excel(writer, sheet_name='By Category', index=False)
        pd.DataFrame(degree_summary).to_excel(writer, sheet_name='By Degree', index=False)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'financial_report_{report_timestamp()}.xlsx'
    )


@app.route('/reports/export/pdf')
def export_reports_pdf():
    category_summary, degree_summary = load_report_summaries()
    if category_summary is None:
        return redirect(url_for('reports'))

    buffer = build_report_pdf(category_summary, degree_summary)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'financial_report_{report_timestamp()}.pdf'
    )

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    current_settings = load_settings()

    if request.method == 'POST':
        current_settings.update({
            'institution_name': request.form.get('institution_name', '').strip(),
            'contact_email': request.form.get('contact_email', '').strip(),
            'contact_phone': request.form.get('contact_phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'backup_schedule': request.form.get('backup_schedule', current_settings['backup_schedule'])
        })
        save_settings(current_settings)
        flash('Institution profile saved.', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', settings=current_settings, excel_file=EXCEL_FILE)

@app.route('/download_backup')
def download_backup():
    file_path = os.path.abspath(EXCEL_FILE)
    if not os.path.exists(file_path):
        flash('Workbook file was not found.', 'danger')
        return redirect(url_for('settings'))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    download_name = f"students_backup_{timestamp}.xlsx"
    return send_file(file_path, as_attachment=True, download_name=download_name)

@app.route('/search_page')
def search_page():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('search_query', '').lower()
    try:
        students = template_students(search_students(query))
    except SupabaseError as exc:
        flash(str(exc), 'danger')
        students = []
    return render_template('results.html', students=students)

@app.route('/details/<reg_no>')
def details(reg_no):
    try:
        student_record = fetch_student(reg_no)
    except SupabaseError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('index'))

    if not student_record:
        flash('Student not found!', 'danger')
        return redirect(url_for('index'))
    
    student = student_to_template(student_record)
    return render_template('details.html', student=student)

@app.route('/pay', methods=['POST'])
def pay():
    reg_no = request.form.get('reg_no')
    mode = request.form.get('mode')
    amount = request.form.get('amount')
    fee_type = request.form.get('type')
    ews_status = request.form.get('ews_status', 'NO')
    
    try:
        amount_val = float(amount)
    except (ValueError, TypeError):
        amount_val = 0.0

    try:
        updated_student = update_payment(reg_no, mode, amount_val, fee_type, ews_status)
    except SupabaseError as exc:
        flash(str(exc), 'danger')
        student_record = fetch_student(reg_no)
        student = student_to_template(student_record) if student_record else {}
        return render_template('details.html', student=student), 423

    if not updated_student:
        flash('Student not found during payment!', 'danger')
        return redirect(url_for('index'))
    
    student = student_to_template(updated_student)
    payment = {
        'receipt_no': f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'amount': amount,
        'mode': mode,
        'type': fee_type
    }
    
    return render_template('bill.html', student=student, payment=payment, settings=load_settings())

if __name__ == '__main__':
    app.run(debug=True, port=5000)
