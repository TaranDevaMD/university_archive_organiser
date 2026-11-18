from flask import Flask, render_template, request, redirect, session, flash, url_for
from datetime import date
import re
import os
import threading
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

users = [
    {'name': 'Admin', 'email': 'admin@college.com', 'password': 'admin123', 'role': 'admin'},
    {'name': 'Prof. Alice', 'email': 'alice@college.com', 'password': 'alice123', 'role': 'teacher'},
    {'name': 'Prof. Bob', 'email': 'bob@college.com', 'password': 'bob123', 'role': 'teacher'}
]
academic_years = ['2023-2024', '2024-2025']
folders_default = ['Namelist', 'Course Files', 'Notes', 'Modules', 'CIA 1', 'Midsem', 'CIA 2', 'Endsem']
subjects = [
    {'name': 'Data Structures', 'code': 'CS3401', 'regulation': 'R2023', 'type': 'Major Course', 'format': 'Theory', 'sem': 3, 'year': '2023-2024', 'teachers': ['alice@college.com']},
    {'name': 'Database Systems', 'code': 'CS3402', 'regulation': 'R2023', 'type': 'Major Course', 'format': 'Theory cum Practical', 'sem': 3, 'year': '2023-2024', 'teachers': ['alice@college.com', 'bob@college.com']},
    {'name': 'Python Programming', 'code': 'CS2401', 'regulation': 'R2023', 'type': 'Minor Course', 'format': 'Practical', 'sem': 2, 'year': '2023-2024', 'teachers': ['bob@college.com']},
    {'name': 'Computer Networks', 'code': 'CS4401', 'regulation': 'R2023', 'type': 'Major Course', 'format': 'Theory', 'sem': 4, 'year': '2024-2025', 'teachers': ['alice@college.com']},
    {'name': 'Web Technology', 'code': 'CS4402', 'regulation': 'R2023', 'type': 'Value Added Course', 'format': 'Practical', 'sem': 4, 'year': '2024-2025', 'teachers': ['bob@college.com']},
    {'name': 'Mathematics', 'code': 'MA1401', 'regulation': 'R2023', 'type': 'Other', 'format': 'Theory', 'sem': 1, 'year': '2024-2025', 'teachers': ['alice@college.com']}
]
folder_names = {}
for subject in subjects:
    folder_names[(subject['year'], subject['sem'], subject['code'])] = folders_default[:]
files = []
categories = folders_default + ['Other']
for i in range(10):
    subject = subjects[i % len(subjects)]
    category = folders_default[i % len(folders_default)]
    name = subject['code'] + '_' + subject['year'] + '_' + category.replace(' ', '') + '_Demo' + str(i + 1) + '.pdf'
    files.append({'name': name, 'category': category, 'type': 'PDF', 'size': '120 KB', 'version': 1,
                  'uploaded_by': users[1 + i % 2]['name'], 'hash': 'demo-hash-' + str(i),
                  'date': '2024-10-01', 'path': subject['year'] + '/Sem ' + str(subject['sem']) + '/' + subject['code'] + '/' + category,
                  'year': subject['year'], 'sem': subject['sem'], 'code': subject['code']})

# Thread lock for mutable global state
_data_lock = threading.Lock()

# Find a subject by its academic year, semester and course code.
def find_subject(year, sem, code):
    for subject in subjects:
        if subject['year'] == year and str(subject['sem']) == str(sem) and subject['code'] == code:
            return subject
    return None

# Make a simple nested dictionary for the folder sidebar.
def make_tree():
    tree = {}
    for year in academic_years:
        tree[year] = {}
        for level in range(1, 5):
            tree[year][str(level) + ('st' if level == 1 else 'nd' if level == 2 else 'rd' if level == 3 else 'th') + ' Year'] = {}
            for sem in (level * 2 - 1, level * 2):
                tree[year][list(tree[year].keys())[-1]]['Sem ' + str(sem)] = {}
    for subject in subjects:
        level = (subject['sem'] + 1) // 2
        level_name = str(level) + ('st' if level == 1 else 'nd' if level == 2 else 'rd' if level == 3 else 'th') + ' Year'
        tree[subject['year']][level_name]['Sem ' + str(subject['sem'])][subject['code'] + ' - ' + subject['name']] = {}
        for folder in folder_names.get((subject['year'], subject['sem'], subject['code']), []):
            tree[subject['year']][level_name]['Sem ' + str(subject['sem'])][subject['code'] + ' - ' + subject['name']][folder] = {}
    return tree

# Read the selected folder and return its immediate items.
def explorer_items(path):
    parts = [part for part in path.split('/') if part]
    node = make_tree()
    for part in parts:
        if part not in node:
            return [], []
        node = node[part]
    shown_files = []
    for file in files:
        pieces = file['path'].split('/')
        if len(parts) >= 4 and len(parts) <= 5 and file['year'] == parts[0] and ('Sem ' + str(file['sem'])) == parts[2] and pieces[2] == parts[3] and (len(parts) == 4 or pieces[3] == parts[4]):
            shown_files.append(file)
    return list(node.keys()), shown_files if len(parts) == 5 else []

# Check whether the signed-in user can use a dashboard.
def allowed(role):
    if not session.get('email'):
        return False
    return session.get('role') == role

# CSRF token generation and validation
def generate_csrf_token():
    if 'csrf_token' not in session:
        import secrets
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']

def validate_csrf_token(token):
    return token and session.get('csrf_token') == token

def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
            if not validate_csrf_token(token):
                flash('Invalid CSRF token', 'danger')
                return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Get filtered files for the shared search page.
def search_files():
    result = []
    for file in files:
        if request.args.get('keyword', '').lower() not in file['name'].lower():
            continue
        if request.args.get('code') and request.args['code'] != file['code']:
            continue
        if request.args.get('year') and request.args['year'] != file['year']:
            continue
        if request.args.get('sem') and request.args['sem'] != str(file['sem']):
            continue
        if request.args.get('category') and request.args['category'] != file['category']:
            continue
        result.append(file)
    return result

# Safe int conversion with default
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

# Open the correct dashboard or the login page.
@app.route('/')
def home():
    if not session.get('email'):
        return redirect(url_for('login'))
    return redirect(url_for('admin' if session['role'] == 'admin' else 'teacher'))

# Sign in with the hardcoded demo accounts.
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        for user in users:
            if user['email'] == request.form.get('email') and user['password'] == request.form.get('password'):
                session['email'], session['name'], session['role'] = user['email'], user['name'], user['role']
                generate_csrf_token()  # Generate CSRF token on login
                flash('Signed in (demo only)', 'success')
                return redirect(url_for('home'))
        flash('Incorrect email or password', 'danger')
    return render_template('login.html')

# Clear the demo login session.
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

# Show the admin controls, search and explorer.
@app.route('/admin')
def admin():
    if not allowed('admin'):
        flash('Admin access only', 'warning')
        return redirect(url_for('home'))
    path = request.args.get('path', '')
    dirs, visible_files = explorer_items(path)
    count_val = request.args.get('count', '1')
    count = min(max(safe_int(count_val, 1), 1), 12)
    return render_template('admin_dashboard.html', years=academic_years, subjects=subjects, teachers=users[1:],
                           files=files, categories=categories, tree=make_tree(), dirs=dirs, visible_files=visible_files,
                           path=path, can_edit=True, matches=search_files(), folders=folder_names,
                           defaults=folders_default, count=count)

# Show teacher controls with only assigned subjects for editing.
@app.route('/teacher')
def teacher():
    if not allowed('teacher'):
        flash('Teacher access only', 'warning')
        return redirect(url_for('home'))
    chosen = request.args.get('subject', '')
    assigned = [s for s in subjects if session['email'] in s['teachers']]
    if chosen and not any(s['code'] == chosen for s in assigned):
        flash('You do not have access to this subject', 'danger')
        return redirect(url_for('teacher'))
    path = request.args.get('path', '')
    dirs, visible_files = explorer_items(path)
    return render_template('teacher_dashboard.html', years=academic_years, subjects=subjects, assigned=assigned,
                           files=files, categories=categories, tree=make_tree(), dirs=dirs, visible_files=visible_files,
                           path=path, can_edit=False, matches=search_files(), folders=folder_names, defaults=folders_default)

# Create an academic year and its empty semester folders.
@app.route('/create-year', methods=['POST'])
@csrf_protect
def create_year():
    if not allowed('admin'):
        return redirect(url_for('home'))
    year = request.form.get('year', '').strip()
    if not re.fullmatch(r'\d{4}-\d{4}', year) or int(year[5:]) != int(year[:4]) + 1:
        flash('Use the format 2023-2024', 'danger')
    elif year in academic_years:
        flash('Academic year already exists', 'danger')
    else:
        academic_years.append(year)
        flash('Academic year and semester folders created (demo only)', 'success')
    return redirect(url_for('admin', action='create', year=year))

# Save the subjects entered in the simple two-step wizard.
@app.route('/save-subjects', methods=['POST'])
@csrf_protect
def save_subjects():
    if not allowed('admin'):
        return redirect(url_for('home'))
    year, sem = request.form.get('year', ''), request.form.get('sem', '')
    if year not in academic_years or not sem.isdigit() or int(sem) not in range(1, 9):
        flash('Choose a valid year and semester', 'danger')
        return redirect(url_for('admin'))
    count = min(safe_int(request.form.get('count', 1), 1), 12)
    for i in range(count):
        code = request.form.get('code_' + str(i), '').strip().upper()
        name = request.form.get('name_' + str(i), '').strip()
        if not code or not name or find_subject(year, int(sem), code):
            flash('A subject was missing a name/code or already exists', 'warning')
            continue
        selected = [email for email in request.form.getlist('teachers_' + str(i)) if any(u['email'] == email for u in users[1:])]
        subject = {'name': name, 'code': code, 'regulation': request.form.get('regulation_' + str(i), ''),
                   'type': request.form.get('type_' + str(i), 'Other'), 'format': request.form.get('format_' + str(i), 'Theory'),
                   'sem': int(sem), 'year': year, 'teachers': selected}
        subjects.append(subject)
        folder_names[(year, int(sem), code)] = folders_default[:]
    flash('Subjects saved (demo only)', 'success')
    return redirect(url_for('admin', action='update'))

# Add a subfolder to a subject.
@app.route('/add-folder', methods=['POST'])
@csrf_protect
def add_folder():
    if not allowed('admin'):
        return redirect(url_for('home'))
    year = request.form.get('year', '')
    sem = safe_int(request.form.get('sem', 1), 1)
    code = request.form.get('code', '')
    key = (year, sem, code)
    name = request.form.get('name', '').strip()
    if key in folder_names and name and '/' not in name and name not in folder_names[key]:
        folder_names[key].append(name)
        flash('Folder added (demo only)', 'success')
    else:
        flash('Invalid or duplicate folder', 'danger')
    return redirect(url_for('admin', action='update'))

# Rename an existing subject subfolder.
@app.route('/rename-folder', methods=['POST'])
@csrf_protect
def rename_folder():
    if not allowed('admin'):
        return redirect(url_for('home'))
    year = request.form.get('year', '')
    sem = safe_int(request.form.get('sem', 1), 1)
    code = request.form.get('code', '')
    key = (year, sem, code)
    old, new = request.form.get('old'), request.form.get('name', '').strip()
    if key in folder_names and old in folder_names[key] and new and '/' not in new and new not in folder_names[key]:
        folder_names[key][folder_names[key].index(old)] = new
        for file in files:
            if file['year'] == key[0] and file['sem'] == key[1] and file['code'] == key[2] and file['category'] == old:
                file['category'] = new
                file['path'] = file['path'].rsplit('/', 1)[0] + '/' + new
        flash('Folder renamed (demo only)', 'success')
    else:
        flash('Could not rename folder', 'danger')
    return redirect(url_for('admin', action='update'))

# Delete a subfolder and its demo file records.
@app.route('/delete-folder', methods=['POST'])
@csrf_protect
def delete_folder():
    if not allowed('admin'):
        return redirect(url_for('home'))
    year = request.form.get('year', '')
    sem = safe_int(request.form.get('sem', 1), 1)
    code = request.form.get('code', '')
    key = (year, sem, code)
    name = request.form.get('name')
    if key in folder_names and name in folder_names[key]:
        with _data_lock:
            folder_names[key].remove(name)
            files[:] = [f for f in files if not (f['year'] == key[0] and f['sem'] == key[1] and f['code'] == key[2] and f['category'] == name)]
        flash('Folder deleted (demo only)', 'success')
    return redirect(url_for('admin', action='update'))

# Copy matching regulation subjects into the chosen academic year.
@app.route('/copy-regulation', methods=['POST'])
@csrf_protect
def copy_regulation():
    if not allowed('admin'):
        return redirect(url_for('home'))
    year, regulation = request.form.get('year'), request.form.get('regulation')
    if year not in academic_years:
        return redirect(url_for('admin'))
    original = [s for s in subjects if s['regulation'] == regulation and s['year'] != year]
    for subject in original:
        if find_subject(year, subject['sem'], subject['code']):
            continue
        copy = subject.copy()
        copy['year'] = year
        copy['teachers'] = subject['teachers'][:]
        subjects.append(copy)
        folder_names[(year, subject['sem'], subject['code'])] = folder_names[(subject['year'], subject['sem'], subject['code'])][:]
        for file in files[:]:
            if file['year'] == subject['year'] and file['sem'] == subject['sem'] and file['code'] == subject['code']:
                new_file = file.copy()
                new_file['year'] = year
                new_file['path'] = year + file['path'][len(subject['year']):]
                files.append(new_file)
    flash('Matching subjects and file records copied (demo only)', 'success')
    return redirect(url_for('admin', action='update'))

# Change the teachers assigned to one subject.
@app.route('/assign-faculty', methods=['POST'])
@csrf_protect
def assign_faculty():
    if not allowed('admin'):
        return redirect(url_for('home'))
    subject = find_subject(request.form.get('year'), request.form.get('sem'), request.form.get('code'))
    if subject:
        subject['teachers'] = [e for e in request.form.getlist('teachers') if any(u['email'] == e for u in users[1:])]
        flash('Faculty updated (demo only)', 'success')
    return redirect(url_for('admin', action='update'))

# Allowed file extensions and max size - shared config
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'pptx', 'xlsx', 'csv', 'jpg', 'jpeg', 'png', 'gif', 'zip'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

# Add a dummy upload record without saving the actual file.
@app.route('/upload', methods=['POST'])
@csrf_protect
def upload():
    if not session.get('email'):
        return redirect(url_for('login'))
    year, sem, code = request.form.get('year'), request.form.get('sem'), request.form.get('code')
    subject = find_subject(year, sem, code)
    if not subject or (session['role'] == 'teacher' and session['email'] not in subject['teachers']):
        flash('You do not have access to this subject', 'danger')
        return redirect(url_for('teacher' if session['role'] == 'teacher' else 'admin'))
    category = request.form.get('category', '')
    folder_key = (year, int(sem), code)
    if folder_key not in folder_names or category not in folder_names[folder_key]:
        flash('Choose a valid folder', 'danger')
        return redirect(url_for('home'))
    filename = request.form.get('final_name', '')
    original = request.files.get('file')
    ext = (original.filename.rsplit('.', 1)[-1].lower() if original and '.' in original.filename else '')
    if not original or ext not in ALLOWED_EXTENSIONS or not filename.lower().endswith('.' + ext):
        flash('Unsupported file type', 'danger')
        return redirect(url_for('home'))
    original.stream.seek(0, 2)
    size = original.stream.tell()
    if size > MAX_FILE_SIZE:
        flash('Maximum file size is 25 MB', 'danger')
        return redirect(url_for('home'))
    hash_value = request.form.get('hash', '')
    if hash_value and any(f['hash'] == hash_value for f in files):
        flash('Duplicate file detected', 'danger')
        return redirect(url_for('home'))
    with _data_lock:
        version = 1 + max([f['version'] for f in files if f['name'] == filename and f['year'] == year and f['sem'] == int(sem) and f['code'] == code] or [0])
        files.append({'name': filename, 'category': category, 'type': ext.upper(), 'size': str(round(size / 1024, 1)) + ' KB',
                      'version': version, 'uploaded_by': session['name'], 'hash': hash_value or 'demo-no-hash',
                      'date': str(date.today()), 'path': year + '/Sem ' + sem + '/' + code + '/' + category,
                      'year': year, 'sem': int(sem), 'code': code})
    flash('Saved (demo only) - Version ' + str(version), 'success')
    return redirect(url_for('teacher', view='upload') if session['role'] == 'teacher' else url_for('admin', action='update'))

# Add a new version of an existing dummy file record.
@app.route('/save-edit', methods=['POST'])
@csrf_protect
def save_edit():
    if not session.get('email'):
        return redirect(url_for('login'))
    year, sem, code, filename = (request.form.get(x, '') for x in ['year', 'sem', 'code', 'filename'])
    subject = find_subject(year, sem, code)
    if not subject or (session['role'] == 'teacher' and session['email'] not in subject['teachers']):
        flash('You do not have access to this subject', 'danger')
        return redirect(url_for('home'))
    matches = [f for f in files if f['name'] == filename and f['year'] == year and str(f['sem']) == sem and f['code'] == code]
    if matches:
        with _data_lock:
            copy = max(matches, key=lambda f: f['version']).copy()
            copy['version'] += 1
            copy['date'] = str(date.today())
            copy['uploaded_by'] = session['name']
            copy['hash'] = 'edited-demo-' + str(len(files))
            files.append(copy)
        flash('Saved as Version ' + str(copy['version']) + ' (demo only)', 'success')
    else:
        flash('Choose an existing file', 'danger')
    return redirect(url_for('teacher', view='edit') if session['role'] == 'teacher' else url_for('admin', action='update'))

# Rename or delete a dummy file record as an admin.
@app.route('/file-action', methods=['POST'])
@csrf_protect
def file_action():
    if not allowed('admin'):
        return redirect(url_for('home'))
    name, year, code, sem = (request.form.get(x, '') for x in ['filename', 'year', 'code', 'sem'])
    selected = [f for f in files if f['name'] == name and f['year'] == year and f['code'] == code and str(f['sem']) == sem]
    if request.form.get('operation') == 'delete':
        with _data_lock:
            files[:] = [f for f in files if f not in selected]
        flash('File records deleted (demo only)', 'success')
    elif request.form.get('operation') == 'rename':
        new = request.form.get('new_name', '').strip()
        if new and '/' not in new:
            for file in selected:
                file['name'] = new
            flash('File renamed (demo only)', 'success')
    return redirect(url_for('admin', action='update'))

if __name__ == '__main__':
    app.run(debug=True)