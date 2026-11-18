/* Read simple JSON that Flask placed on the page. */
function readData(id) {
    const item = document.getElementById(id);
    return item ? JSON.parse(item.textContent) : [];
}

/* Open and download are only messages because files are not stored. */
function demoOpen(name) { alert('Demo preview only: ' + name + '\nNo real file is stored.'); }
function demoDownload(name) { alert('Demo download only: ' + name + '\nNo real file is stored.'); }

/* Filter the currently visible explorer cards. */
function filterExplorer() {
    const value = document.getElementById('explorerSearch').value.toLowerCase();
    document.querySelectorAll('.explorer-item').forEach(item => {
        item.classList.toggle('d-none', !item.dataset.name.includes(value));
    });
}

/* Switch the explorer between cards and a simple details list. */
function setExplorerView(view) {
    document.getElementById('explorerItems').classList.toggle('list-mode', view === 'list');
}

/* Display the selected file's details and all its demo versions. */
function showDetails(name, category, uploader, version, hash) {
    document.getElementById('detailName').textContent = 'Name: ' + name;
    document.getElementById('detailCategory').textContent = 'Category: ' + category;
    document.getElementById('detailUploader').textContent = 'Uploaded by: ' + uploader;
    document.getElementById('detailVersion').textContent = 'Version: ' + version;
    document.getElementById('detailHash').textContent = 'SHA-256 / Demo hash: ' + hash;
    const list = document.getElementById('detailHistory');
    list.replaceChildren();
    readData('explorerData').filter(file => file.name === name).forEach(file => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.textContent = 'Version ' + file.version + ' - ' + file.date + ' (' + file.uploaded_by + ')';
        list.appendChild(li);
    });
    const offcanvas = document.getElementById('fileDetails');
    if (offcanvas) {
        const bsOffcanvas = bootstrap.Offcanvas.getOrCreateInstance(offcanvas);
        bsOffcanvas.show();
    }
}

let contextItem = null;
/* Open the context menu when a file is right-clicked. */
function showContext(event, item) {
    event.preventDefault();
    contextItem = item;
    const menu = document.getElementById('contextMenu');
    menu.style.left = Math.min(event.clientX, window.innerWidth - 180) + 'px';
    menu.style.top = Math.min(event.clientY, window.innerHeight - 220) + 'px';
    menu.classList.remove('d-none');
    return false;
}

/* Hide the context menu when clicking outside it. */
document.addEventListener('click', event => {
    const menu = document.getElementById('contextMenu');
    if (menu && !menu.contains(event.target)) menu.classList.add('d-none');
});

/* Use the visible file buttons for context menu actions. */
function contextButton(text) {
    if (!contextItem) return;
    const button = Array.from(contextItem.querySelectorAll('button')).find(b => b.textContent.trim() === text);
    if (button) button.click();
}
function contextOpen() { contextButton('Open'); }
function contextDownload() { contextButton('Download'); }
function contextDetails() { contextButton('Details'); }
function contextRename() { contextButton('Rename'); }
function contextDelete() { contextButton('Delete'); }
/* New folders are managed using the admin folder form below the explorer. */
function contextNewFolder() { alert('Use Manage Subject Folders below to create a new folder.'); }

/* Submit a simple admin file rename or delete. */
function fileAction(operation, filename, year, code, sem) {
    const form = document.getElementById('fileActionForm');
    if (!form) return;
    let newName = '';
    if (operation === 'rename') {
        newName = prompt('New file name:', filename);
        if (!newName) return;
    } else if (!confirm('Delete demo file records?')) return;
    ['operation', 'filename', 'year', 'code', 'sem', 'new_name'].forEach((key, i) => {
        form.elements[key].value = [operation, filename, year, code, sem, newName][i];
    });
    form.submit();
}

let wizardStep = 0;
/* Move through subject forms and finally show a review table. */
function wizardMove(change) {
    const steps = Array.from(document.querySelectorAll('.subject-step'));
    if (!steps.length) return;
    if (change > 0 && wizardStep < steps.length) {
        const fields = steps[wizardStep].querySelectorAll('input[required]');
        for (const field of fields) if (!field.reportValidity()) return;
    }
    wizardStep = Math.max(0, Math.min(steps.length, wizardStep + change));
    steps.forEach((step, i) => step.classList.toggle('d-none', i !== wizardStep));
    const reviewing = wizardStep === steps.length;
    document.getElementById('wizardReview').classList.toggle('d-none', !reviewing);
    document.getElementById('wizardNext').classList.toggle('d-none', reviewing);
    document.getElementById('wizardSave').classList.toggle('d-none', !reviewing);
    document.getElementById('wizardBack').disabled = wizardStep === 0;
    const percent = Math.round(100 * wizardStep / steps.length);
    const progress = document.getElementById('wizardProgress');
    progress.style.width = percent + '%';
    progress.textContent = percent + '%';
    if (reviewing) {
        const rows = document.getElementById('reviewRows');
        rows.replaceChildren();
        steps.forEach(step => {
            const fields = ['name_', 'code_', 'regulation_', 'type_', 'format_', 'teachers_'];
            const tr = document.createElement('tr');
            fields.forEach(field => {
                const el = step.querySelector('[name^="' + field + '"]');
                const td = document.createElement('td');
                td.textContent = el.multiple ? Array.from(el.selectedOptions).map(o => o.text).join(', ') : el.value;
                tr.appendChild(td);
            });
            rows.appendChild(tr);
        });
    }
}

/* Show only subjects belonging to the selected regulation. */
function showRegulationMatches() {
    const select = document.getElementById('regulationChoice');
    if (!select) return;
    document.querySelectorAll('[data-regulation]').forEach(row => {
        row.classList.toggle('d-none', row.dataset.regulation !== select.value);
    });
}

/* Fill a select box with a new set of options. */
function fillSelect(select, values, placeholder) {
    select.replaceChildren(new Option(placeholder, ''));
    values.forEach(value => select.add(new Option(value.label || value, value.value || value)));
}

/* Update the cascading year, semester, subject and folder selectors. */
function updateCascade(form, changed) {
    const assigned = readData('assignedData');
    const folderData = readData('subjectFolders');
    const year = form.querySelector('.cascade-year');
    const sem = form.querySelector('.cascade-sem');
    const subject = form.querySelector('.cascade-subject');
    const folder = form.querySelector('.cascade-folder');
    if (changed === 'start') fillSelect(year, [...new Set(assigned.map(s => s.year))], 'Choose year');
    if (changed === 'start' || changed === 'year') {
        fillSelect(sem, [...new Set(assigned.filter(s => s.year === year.value).map(s => s.sem))].sort((a,b) => a-b).map(n => ({label: 'Sem ' + n, value: String(n)})), 'Choose semester');
    }
    if (['start', 'year', 'sem'].includes(changed)) {
        fillSelect(subject, assigned.filter(s => s.year === year.value && String(s.sem) === sem.value).map(s => ({label: s.code + ' - ' + s.name, value: s.code})), 'Choose subject');
    }
    if (['start', 'year', 'sem', 'subject'].includes(changed)) {
        const match = folderData.find(s => s.year === year.value && String(s.sem) === sem.value && s.code === subject.value);
        fillSelect(folder, match ? match.folders : [], 'Choose folder');
    }
    if (form.dataset.mode === 'upload') updatePreview();
    if (form.dataset.mode === 'edit') updateEditFiles();
}

/* Build the preview filename from the selected course and category. */
function updatePreview() {
    const form = document.getElementById('uploadForm');
    if (!form) return;
    const file = document.getElementById('uploadFile').files[0];
    const code = form.elements.code.value;
    const year = form.elements.year.value;
    const category = form.elements.category.value.replace(/\s+/g, '');
    const title = (form.elements.title.value.trim() || 'Material').replace(/[^a-zA-Z0-9]/g, '');
    const ext = file ? file.name.split('.').pop().toLowerCase() : '';
    const name = file && code && year && category ? [code, year, category, title].join('_') + '.' + ext : '';
    document.getElementById('uploadPreview').textContent = name || 'Choose a file and subject';
    document.getElementById('finalName').value = name;
}

/* Check the file size and extension before a demo upload. */
function checkFile() {
    const file = document.getElementById('uploadFile').files[0];
    const alertBox = document.getElementById('uploadAlert');
    alertBox.classList.add('d-none');
    if (!file) return false;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf','docx','pptx','xlsx','csv','jpg','jpeg','png','gif','zip'].includes(ext) || file.size > 25 * 1024 * 1024) {
        alertBox.textContent = 'Invalid file type or file exceeds 25 MB.';
        alertBox.classList.remove('d-none');
        return false;
    }
    return true;
}

/* Web Crypto reads the chosen file and calculates its SHA-256 hash. */
async function prepareUpload() {
    const form = document.getElementById('uploadForm');
    if (!checkFile() || !form.reportValidity()) return;
    const file = document.getElementById('uploadFile').files[0];
    const alertBox = document.getElementById('uploadAlert');
    const buffer = await file.arrayBuffer();
    const digest = await crypto.subtle.digest('SHA-256', buffer);
    const hash = Array.from(new Uint8Array(digest)).map(n => n.toString(16).padStart(2, '0')).join('');
    document.getElementById('fileHash').value = hash;
    const all = readData('allFileData');
    const duplicate = all.find(item => item.hash === hash);
    if (duplicate) {
        alertBox.textContent = 'Duplicate file already exists at: ' + duplicate.path;
        alertBox.classList.remove('d-none');
        return;
    }
    const name = document.getElementById('finalName').value;
    const same = all.filter(item => item.name === name && item.year === form.elements.year.value && String(item.sem) === form.elements.sem.value && item.code === form.elements.code.value);
    if (same.length) {
        const version = Math.max(...same.map(item => item.version)) + 1;
        document.getElementById('versionText').textContent = 'This file already exists. It will be saved as Version ' + version + '.';
        const modal = document.getElementById('versionModal');
        if (modal) {
            bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    } else form.submit();
}

/* List files from the selected assigned folder for editing. */
function updateEditFiles() {
    const form = document.getElementById('editForm');
    if (!form) return;
    const matches = readData('allFileData').filter(f => f.year === form.elements.year.value && String(f.sem) === form.elements.sem.value && f.code === form.elements.code.value && f.category === form.elements.category.value);
    fillSelect(document.getElementById('editFile'), [...new Set(matches.map(f => f.name))], 'Choose file');
    updateEditHistory();
}

/* Display all demo versions of the chosen file. */
function updateEditHistory() {
    const form = document.getElementById('editForm');
    if (!form) return;
    const list = document.getElementById('editHistory');
    list.replaceChildren();
    readData('allFileData').filter(f => f.name === form.elements.filename.value && f.year === form.elements.year.value && f.code === form.elements.code.value).forEach(f => {
        const li = document.createElement('li');
        li.className = 'list-group-item';
        li.textContent = 'Version ' + f.version + ' - ' + f.date;
        list.appendChild(li);
    });
}

/* Insert simple formatting marks around selected editor text. */
function insertText(before, after) {
    const box = document.getElementById('editText');
    const start = box.selectionStart, end = box.selectionEnd;
    box.setRangeText(before + box.value.slice(start, end) + after, start, end, 'select');
    box.focus();
}

/* Set up the forms when the page is ready. */
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.subject-step')) wizardMove(0);
    showRegulationMatches();
    document.querySelectorAll('[data-mode]').forEach(form => {
        updateCascade(form, 'start');
        ['year','sem','code','category'].forEach((key, i) => {
            form.elements[key].addEventListener('change', () => updateCascade(form, ['year','sem','subject','folder'][i]));
        });
    });
    const upload = document.getElementById('uploadFile');
    if (upload) {
        upload.addEventListener('change', () => { checkFile(); updatePreview(); });
        document.getElementById('uploadTitle').addEventListener('input', updatePreview);
        const zone = document.getElementById('dropZone');
        zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragging'); });
        zone.addEventListener('dragleave', () => zone.classList.remove('dragging'));
        zone.addEventListener('drop', e => {
            e.preventDefault(); zone.classList.remove('dragging');
            upload.files = e.dataTransfer.files; checkFile(); updatePreview();
        });
    }
    const edit = document.getElementById('editFile');
    if (edit) edit.addEventListener('change', updateEditHistory);
});

/* Fill the admin upload form from the chosen subject. */
function adminUploadChoice() {
    const form = document.getElementById('adminUpload');
    const select = document.getElementById('adminSubject');
    if (!form || !select.value) return;
    const subject = readData('adminSubjects')[Number(select.value)];
    form.elements.year.value = subject.year;
    form.elements.sem.value = subject.sem;
    form.elements.code.value = subject.code;
    fillSelect(document.getElementById('adminFolder'), subject.folders, 'Choose folder');
    const file = document.getElementById('adminFile').files[0];
    form.elements.final_name.value = file ? file.name : '';
}