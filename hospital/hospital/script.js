const API_BASE = 'http://localhost:5000/api';

let selectedDoctor = null;
let doctorsList = [];
let authToken = localStorage.getItem('token') || '';
let currentUser = JSON.parse(localStorage.getItem('user') || 'null');
let currentActivePatientObj = null;

document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    loadDoctors();
    if (authToken) {
        refreshDoctorDashboard();
        loadMedications();
    }
});

// Live Logger Helper
function logApiCall(method, endpoint, status, responseData) {
    const logBox = document.getElementById('api-log-box');
    const time = new Date().toLocaleTimeString();
    const text = `[${time}] ${method} ${endpoint} -> Status: ${status}\nResponse: ${JSON.stringify(responseData, null, 2)}\n----------------------------------------\n`;
    logBox.innerText = text + logBox.innerText;
}

// Tab Switching
function showTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    const btn = document.getElementById(`tab-${tabName}-btn`);
    if (btn) btn.classList.add('active');
    
    const content = document.getElementById(`${tabName}-tab`);
    if (content) content.classList.add('active');

    if (tabName === 'doctor') refreshDoctorDashboard();
    if (tabName === 'patient') loadMedications();
}

// Quick Login
function quickLogin(email, password) {
    fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('POST', '/api/auth/login', status, data);
        if (status === 200) {
            authToken = data.access_token;
            currentUser = {
                id: data.user_id,
                full_name: data.full_name,
                role: data.role,
                email: data.email
            };
            localStorage.setItem('token', authToken);
            localStorage.setItem('user', JSON.stringify(currentUser));
            updateAuthUI();
            
            // Switch tabs according to role automatically
            if (currentUser.role === 'doctor') showTab('doctor');
            else if (currentUser.role === 'admin') showTab('admin');
            else showTab('patient');

            refreshDoctorDashboard();
            loadMedications();
        } else {
            alert(`فشل تسجيل الدخول: ${data.detail || data.message}`);
        }
    })
    .catch(err => alert("خطأ في شبكة الاتصال بالسيرفر"));
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    authToken = '';
    currentUser = null;
    updateAuthUI();
    showTab('patient');
}

function updateAuthUI() {
    const authStatusEl = document.getElementById('auth-status');
    const logoutBtn = document.getElementById('logout-btn');
    if (authToken && currentUser) {
        authStatusEl.innerHTML = `
            <span>أهلاً وسهلاً، <strong>${currentUser.full_name}</strong></span>
            <span class="role-badge ${currentUser.role}">${currentUser.role === 'patient' ? 'مريض 🧑‍⚕️' : (currentUser.role === 'doctor' ? 'طبيب 👨‍⚕️' : 'أدمن 🛡️')}</span>
        `;
        logoutBtn.style.display = 'inline-block';
    } else {
        authStatusEl.innerHTML = `<span>المستخدم الحالي: <strong>زائر (غير مسجل)</strong></span>`;
        logoutBtn.style.display = 'none';
    }
}

function getAuthHeaders() {
    return authToken ? { 'Authorization': `Bearer ${authToken}` } : {};
}

// ================= DOCTORS & BOOKING =================
function loadDoctors() {
    fetch(`${API_BASE}/doctors`)
        .then(res => res.json().then(data => ({ status: res.status, data })))
        .then(({ status, data }) => {
            logApiCall('GET', '/api/doctors', status, data);
            document.getElementById('doctors-loading').style.display = 'none';
            if (data.success && data.data.length > 0) {
                doctorsList = data.data;
                const grid = document.getElementById('doctors-grid');
                grid.style.display = 'grid';
                grid.innerHTML = doctorsList.map(doc => `
                    <div class="doctor-card" onclick="selectDoctor('${doc.id}')" id="doc-card-${doc.id}">
                        <h4>👨‍⚕️ ${doc.name}</h4>
                        <div class="spec">التخصص: ${doc.specialization}</div>
                        <div class="bio">${doc.bio || 'طبيب أخصائي بالعيادة'}</div>
                    </div>
                `).join('');
            }
        });
}

function selectDoctor(docId) {
    selectedDoctor = doctorsList.find(d => d.id === docId);
    document.querySelectorAll('.doctor-card').forEach(c => c.classList.remove('selected'));
    document.getElementById(`doc-card-${docId}`).classList.add('selected');

    document.getElementById('selected-doctor-banner').innerHTML = `
        <div style="background:rgba(52,211,153,0.1); border:1px solid var(--accent-emerald); padding:12px; border-radius:12px; margin-bottom:12px;">
            🩺 الطبيب المختار للحجز: <strong>${selectedDoctor.name}</strong> (${selectedDoctor.specialization})
        </div>
    `;
    document.getElementById('booking-form-section').style.display = 'block';

    // Auto fill name/phone if logged in as patient
    if (currentUser && currentUser.role === 'patient') {
        document.getElementById('patient-name').value = currentUser.full_name;
    }
}

function backToDoctorSelection() {
    document.getElementById('booking-form-section').style.display = 'none';
    selectedDoctor = null;
    document.querySelectorAll('.doctor-card').forEach(c => c.classList.remove('selected'));
}

document.getElementById('booking-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('patient-name').value;
    const phone = document.getElementById('patient-phone').value;

    fetch(`${API_BASE}/book`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name, phone, doctor_id: selectedDoctor ? selectedDoctor.id : null
        })
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('POST', '/api/book', status, data);
        if (data.success) {
            const b = data.data;
            document.getElementById('queue-number').innerText = b.queueNumber;
            document.getElementById('estimated-time').innerText = b.estimatedTime;
            document.getElementById('waiting-count').innerText = b.waitingCount;

            document.getElementById('doctor-selection-section').style.display = 'none';
            document.getElementById('booking-form-section').style.display = 'none';
            document.getElementById('confirmation-section').style.display = 'block';
            refreshDoctorDashboard();
        } else {
            alert(data.message || 'فشل الحجز');
        }
    });
});

function newBooking() {
    document.getElementById('confirmation-section').style.display = 'none';
    document.getElementById('doctor-selection-section').style.display = 'block';
    backToDoctorSelection();
    loadDoctors();
}

// ================= DOCTOR DASHBOARD & AUTOMATIC PATIENT TRACKING =================
function refreshDoctorDashboard() {
    const headers = getAuthHeaders();

    // 1. Fetch Statistics
    fetch(`${API_BASE}/stats`, { headers })
        .then(res => res.json().then(data => ({ status: res.status, data })))
        .then(({ status, data }) => {
            logApiCall('GET', '/api/stats', status, data);
            if (status === 200 && data.success) {
                const s = data.data;
                document.getElementById('total-patients').innerText = s.totalPatients;
                document.getElementById('waiting-patients').innerText = s.waitingPatients;
                document.getElementById('completed-patients').innerText = s.completedPatients;
                document.getElementById('current-patient-queue').innerText = s.currentPatient || '--';
            }
        });

    // 2. Fetch Patients Queue Table & Identify Active Patient Automatically
    fetch(`${API_BASE}/patients`, { headers })
        .then(res => res.json().then(data => ({ status: res.status, data })))
        .then(({ status, data }) => {
            logApiCall('GET', '/api/patients', status, data);
            const tbody = document.getElementById('patients-tbody');
            const activeBox = document.getElementById('active-patient-box');

            if (status === 403) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#fb7185; padding:16px;">🔒 403 Forbidden: سجل الدخول كـ (طبيب أو أدمن) لعرض لوحة العيادة.</td></tr>`;
                activeBox.innerHTML = `<p style="text-align:center; color:#fb7185;">🔒 المحتوى محمي. سجل الدخول كـ طبيب لمشاهدة المريض الحالي.</p>`;
                return;
            }

            if (data.data && Array.isArray(data.data)) {
                const patients = data.data;
                if (patients.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" class="no-data">لا توجد حجوزات اليوم حتى الآن</td></tr>`;
                    activeBox.innerHTML = `<p style="text-align:center; color:var(--text-muted); padding:16px;">☕ لا يوجد مرضى في غرفة الكشف الآن.</p>`;
                    currentActivePatientObj = null;
                } else {
                    // Find first patient whose status is 'waiting' (Pending)
                    const activeAppt = patients.find(p => p.status === 'waiting');
                    if (activeAppt) {
                        currentActivePatientObj = activeAppt;
                        renderActivePatientCard(activeAppt);
                    } else {
                        currentActivePatientObj = null;
                        activeBox.innerHTML = `
                            <div style="text-align:center; color:var(--accent-emerald); padding:16px;">
                                🎉 تم الانتهاء من جميع كشوفات المرضى لليوم بنجاح!
                            </div>
                        `;
                    }

                    // Render Table
                    tbody.innerHTML = patients.map(p => `
                        <tr style="${p.status === 'waiting' && activeAppt && p.id === activeAppt.id ? 'background:rgba(56,189,248,0.1); border-right:4px solid var(--accent-blue);' : ''}">
                            <td><strong>#${p.queueNumber}</strong></td>
                            <td>
                                <strong>${p.name}</strong>
                                ${p.status === 'waiting' && activeAppt && p.id === activeAppt.id ? '<span style="color:var(--accent-blue); font-size:0.8rem; margin-right:6px;">(داخل الغرفة الآن 🩺)</span>' : ''}
                            </td>
                            <td>${p.phone}</td>
                            <td>${p.estimatedTime}</td>
                            <td>
                                <span class="status-badge ${p.status}">
                                    ${p.status === 'waiting' ? '⏳ في الانتظار' : '✅ تم الكشف ومشي'}
                                </span>
                            </td>
                            <td>
                                ${p.status === 'waiting' ? `
                                    <button class="btn-primary" style="padding:4px 10px; font-size:0.8rem;" onclick="markDone('${p.id}')">إنهاء الكشف ✅</button>
                                ` : '<span style="color:#94a3b8; font-size:0.85rem;">مكتمل</span>'}
                            </td>
                        </tr>
                    `).join('');
                }
            }
        });
}

function renderActivePatientCard(appt) {
    const activeBox = document.getElementById('active-patient-box');
    activeBox.innerHTML = `
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:16px; margin-bottom:16px;">
            <div>
                <small style="color:var(--text-muted);">اسم المريض:</small>
                <div style="font-size:1.3rem; font-weight:800; color:#fff;">👤 ${appt.name}</div>
            </div>
            <div>
                <small style="color:var(--text-muted);">رقم الدور:</small>
                <div style="font-size:1.3rem; font-weight:800; color:var(--accent-blue);">🎫 دور رقم #${appt.queueNumber}</div>
            </div>
            <div>
                <small style="color:var(--text-muted);">رقم الهاتف:</small>
                <div style="font-size:1.1rem; color:var(--text-main);">📱 ${appt.phone}</div>
            </div>
            <div>
                <small style="color:var(--text-muted);">الوقت المتوقع:</small>
                <div style="font-size:1.1rem; color:var(--accent-emerald);">⏰ ${appt.estimatedTime}</div>
            </div>
        </div>

        <div style="display:flex; gap:10px; flex-wrap:wrap; border-top:1px solid var(--border-color); padding-top:16px;">
            <button class="btn-primary" onclick="openDiagnosisDialog('${appt.name}')">🩺 تسجيل التشخيص والروشتة</button>
            <button class="btn-secondary" onclick="openSecretNoteDialog('${appt.name}')">🔒 إضافة ملاحظة سرية للطبيب</button>
            <button class="btn-secondary" style="background:rgba(139,92,246,0.2); border-color:#8b5cf6; color:#8b5cf6;" onclick="viewPatientRecord('${appt.id}', '${appt.name}')">📂 عرض السجل الطبي للمريض</button>
            <button class="btn-danger" style="margin-right:auto;" onclick="markDone('${appt.id}')">✅ إنهاء الكشف والمغادرة</button>
        </div>

        <!-- Medical Record Result Area -->
        <div id="patient-record-box" style="display:none; margin-top:16px; background:#0f172a; border:1px solid #8b5cf6; border-radius:10px; padding:16px;">
            <h4 style="color:#8b5cf6; margin-bottom:8px;">📂 السجل الطبي للمريض</h4>
            <div id="patient-record-content" style="font-family:monospace; color:#e2e8f0; font-size:0.85rem; white-space:pre-wrap;"></div>
        </div>
    `;
}

function viewPatientRecord(patientId, patientName) {
    const box = document.getElementById('patient-record-box');
    const content = document.getElementById('patient-record-content');
    box.style.display = 'block';
    content.innerHTML = '<span style="color:#94a3b8;">⏳ جاري جلب الملفات الطبية المرفوعة...</span>';

    fetch(`${API_BASE}/files/patient/${patientId}`, { headers: getAuthHeaders() })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('GET', `/api/files/patient/${patientId}`, status, data);
        if (status === 200) {
            const files = data.files || [];
            if (files.length === 0) {
                content.innerHTML = `
                    <div style="text-align:center; padding:16px; color:#94a3b8;">
                        📭 لا توجد ملفات طبية مرفوعة لهذا المريض حتى الآن.
                    </div>`;
            } else {
                const fileCards = files.map(f => {
                    const icon = f.content_type?.includes('image') ? '🖼️' :
                                 f.content_type?.includes('pdf') ? '📄' : '📎';
                    const sizekb = (f.size_bytes / 1024).toFixed(1);
                    return `
                    <div style="background:#1e293b; border:1px solid #475569; border-radius:8px; padding:12px; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <div>
                            <div style="font-size:1.1rem;">${icon} <strong>${f.filename}</strong></div>
                            <div style="color:#94a3b8; font-size:0.8rem; margin-top:4px;">
                                نوع الملف: ${f.content_type || 'غير معروف'} &nbsp;|&nbsp; 
                                الحجم: ${sizekb} KB &nbsp;|&nbsp;
                                تاريخ الرفع: ${f.uploaded_at?.substring(0, 16).replace('T', ' ') || '--'}
                            </div>
                        </div>
                        <span style="background:rgba(52,211,153,0.1); color:var(--accent-emerald); padding:4px 10px; border-radius:20px; font-size:0.75rem;">مرفوع ✅</span>
                    </div>`;
                }).join('');

                content.innerHTML = `
                    <strong style="color:var(--accent-emerald);">✅ الملفات الطبية للمريض: ${patientName} (${files.length} ملف)</strong>
                    <div style="margin-top:12px;">${fileCards}</div>`;
            }
        } else if (status === 403) {
            content.innerHTML = `<span style="color:#fb7185;">🔒 403 Forbidden: يجب تسجيل الدخول كطبيب لعرض ملفات المريض.</span>`;
        } else {
            content.innerHTML = `<span style="color:#fb7185;">⚠️ ${data.detail || data.message || 'حدث خطأ أثناء جلب الملفات.'}</span>`;
        }
    });
}



function openDiagnosisDialog(patientName) {
    const diagnosis = prompt(`أدخل التشخيص الطبي والروشتة للمريض (${patientName}):`, "كشف طبي عاجل - المريض يعاني من إجهاد، تم وصف فيتامينات.");
    if (!diagnosis) return;
    alert(`✅ تم تسجيل الروشتة والتشخيص الطبي للمريض ${patientName} بنجاح!`);
}

function openSecretNoteDialog(patientName) {
    const note = prompt(`أدخل ملاحظة سرية خاصة بالعيادة للمريض (${patientName}):`, "ملاحظة: المريض يتابع الضغط بانتظام.");
    if (!note) return;
    alert(`🔒 تم حفظ الملاحظة السرية للمريض ${patientName} بنجاح.`);
}

function markDone(apptId) {
    fetch(`${API_BASE}/patient/${apptId}/done`, {
        method: 'PUT',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' }
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('PUT', `/api/patient/${apptId}/done`, status, data);
        refreshDoctorDashboard();
    });
}

// ================= MEDICATIONS & AUTOMATIC TELEGRAM REMINDER =================
document.getElementById('medication-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const name = document.getElementById('med-name').value;
    const dosage = document.getElementById('med-dosage').value;

    const timeInputs = [
        document.getElementById('med-time-1').value,
        document.getElementById('med-time-2').value,
        document.getElementById('med-time-3').value
    ].filter(t => t); // Get non-empty times

    fetch(`${API_BASE}/medications/`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, dosage, frequency: "مرة يومياً" })
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('POST', '/api/medications/', status, data);
        if (status === 200 || status === 201) {
            const medId = data.id || data.data?.id; // Depends on response schema
            
            // if times are provided, send them
            if (timeInputs.length > 0 && medId) {
                const remindersBody = timeInputs.map(t => ({ reminder_time: t + ":00" }));
                fetch(`${API_BASE}/medications/${medId}/reminders`, {
                    method: 'POST',
                    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
                    body: JSON.stringify(remindersBody)
                })
                .then(r => r.json())
                .then(remData => {
                    logApiCall('POST', `/api/medications/${medId}/reminders`, 201, remData);
                    alert(`✅ تم إضافة الدواء (${name}) وتعيين ${timeInputs.length} موعد תذكير بنجاح!`);
                    document.getElementById('medication-form').reset();
                    loadMedications();
                });
            } else {
                alert(`✅ تم إضافة الدواء (${name}) بنجاح للمريض!`);
                document.getElementById('medication-form').reset();
                loadMedications();
            }
        } else {
            alert(data.detail || data.message || "سجل الدخول كـ مريض أولاً");
        }
    });
});

window.activeMedicationReminders = []; // Used for the frontend scheduler

function loadMedications() {
    fetch(`${API_BASE}/medications/`, { headers: getAuthHeaders() })
        .then(res => res.json().then(data => ({ status: res.status, data })))
        .then(({ status, data }) => {
            logApiCall('GET', '/api/medications/', status, data);
            const tbody = document.getElementById('medications-tbody');
            if (status === 200 && Array.isArray(data)) {
                
                // Construct the active reminders list for local scheduler
                window.activeMedicationReminders = data.map(m => {
                    const times = (m.reminders || []).map(r => r.reminder_time.substring(0, 5));
                    return { name: m.medicine_name, times };
                });

                if (data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="4" class="no-data">لا توجد أدوية مضافة بعد</td></tr>`;
                } else {
                    tbody.innerHTML = data.map(m => {
                        const timesList = (m.reminders || []).map(r => `<span style="background:var(--accent-emerald); color:#000; padding:2px 6px; border-radius:4px; font-size:0.75rem; margin-left:4px;">${r.reminder_time.substring(0, 5)}</span>`).join('');
                        
                        return `
                        <tr>
                            <td><strong>${m.medicine_name}</strong><br><small style="color:var(--text-muted);">الأوقات: ${timesList || 'لم تحدد'}</small></td>
                            <td>${m.dosage || '--'}</td>
                            <td>
                                <button class="btn-secondary" style="padding:4px 10px; font-size:0.8rem;" onclick="triggerDirectReminder('${m.medicine_name}')">
                                    📲 إرسال اختبار فوري
                                </button>
                            </td>
                            <td>
                                <button class="btn-danger" style="padding:4px 8px; font-size:0.75rem;" onclick="deleteMedication('${m.id}')">حذف</button>
                            </td>
                        </tr>
                    `}).join('');
                }
            } else {
                tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#fb7185;">سجل الدخول كـ مريض لعرض أدويتك</td></tr>`;
            }
        });
}

// ----------------------------------------------------
// FRONTEND AUTO-SCHEDULER LOOP (Checks every 15 seconds)
// ----------------------------------------------------
let lastTriggeredMinute = null;
setInterval(() => {
    if (!currentUser || currentUser.role !== 'patient') return;

    const now = new Date();
    const currentMinuteStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
    
    const statusEl = document.getElementById('auto-scheduler-status');
    if (statusEl) {
        statusEl.innerHTML = `⏳ جاري التحقق من المواعيد... (الوقت الحالي: <strong style="color:#fff;">${currentMinuteStr}</strong>)`;
    }

    if (lastTriggeredMinute === currentMinuteStr) return; // Prevent spam within the same minute

    let triggeredAny = false;
    window.activeMedicationReminders.forEach(med => {
        if (med.times.includes(currentMinuteStr)) {
            triggerDirectReminder(med.name);
            triggeredAny = true;
        }
    });

    if (triggeredAny) {
        lastTriggeredMinute = currentMinuteStr;
    }
}, 15000); // Check every 15 seconds


function triggerDirectReminder(medName) {
    // Sends telegram notification automatically based on logged in user's phone or default channel
    fetch(`${API_BASE}/telegram/send-reminder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            chat_id: "default",
            message: `⏰ تذكير آلي: حان الآن ميعاد الجرعة لدواء (${medName}). نتمنى لك دوام الصحة والعافية!`
        })
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('POST', '/api/telegram/send-reminder', status, data);
        alert(`📲 تم إرسال تذكير الجرعة لدواء (${medName}) تلقائياً بنجاح!`);
    });
}

function deleteMedication(id) {
    fetch(`${API_BASE}/medications/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('DELETE', `/api/medications/${id}`, status, data);
        loadMedications();
    });
}

// ================= ADMIN WORKSPACE =================
function fetchAdminUsers() {
    fetch(`${API_BASE}/admin/users`, { headers: getAuthHeaders() })
        .then(res => res.json().then(data => ({ status: res.status, data })))
        .then(({ status, data }) => {
            logApiCall('GET', '/api/admin/users', status, data);
            const container = document.getElementById('admin-results-container');
            container.style.display = 'block';
            const head = document.getElementById('admin-table-head');
            const body = document.getElementById('admin-table-body');

            if (status === 403) {
                head.innerHTML = '';
                body.innerHTML = `<tr><td style="color:#fb7185; text-align:center; padding:16px;">🔒 403 Forbidden: سجل الدخول كـ أدمن أولاً.</td></tr>`;
                return;
            }

            head.innerHTML = `<tr><th>الاسم</th><th>البريد</th><th>الدور</th><th>الحالة</th></tr>`;
            body.innerHTML = data.map(u => `
                <tr>
                    <td>${u.full_name}</td>
                    <td>${u.email}</td>
                    <td><span class="role-badge ${u.role}">${u.role}</span></td>
                    <td>${u.is_active ? '✅ مفعّل' : '❌ معطّل'}</td>
                </tr>
            `).join('');
        });
}

function fetchAuditLogs() {
    fetch(`${API_BASE}/admin/audit-logs`, { headers: getAuthHeaders() })
        .then(res => res.json().then(data => ({ status: res.status, data })))
        .then(({ status, data }) => {
            logApiCall('GET', '/api/admin/audit-logs', status, data);
            const container = document.getElementById('admin-results-container');
            container.style.display = 'block';
            const head = document.getElementById('admin-table-head');
            const body = document.getElementById('admin-table-body');

            if (status === 403) {
                head.innerHTML = '';
                body.innerHTML = `<tr><td style="color:#fb7185; text-align:center; padding:16px;">🔒 403 Forbidden: سجل الدخول كـ أدمن أولاً.</td></tr>`;
                return;
            }

            head.innerHTML = `<tr><th>الحدث</th><th>المستخدم</th><th>التاريخ</th></tr>`;
            body.innerHTML = data.map(l => `
                <tr>
                    <td><strong>${l.action}</strong></td>
                    <td>${l.user_email || 'System'}</td>
                    <td>${l.created_at || '--'}</td>
                </tr>
            `).join('');
        });
}

function clearAllData() {
    if (!confirm("تأكيد مسح كافة الحجوزات (أدمن فقط)؟")) return;
    fetch(`${API_BASE}/patients`, {
        method: 'DELETE',
        headers: getAuthHeaders()
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('DELETE', '/api/patients', status, data);
        alert(data.message || (status === 403 ? 'غير مصرح لك (تحتاج صلاحية أدمن)' : 'تم الحذف'));
        refreshDoctorDashboard();
    });
}

// ================= NEW ENDPOINTS (CHATBOT, FILES, RECORDS) =================

// Chatbot functionality
document.getElementById('chatbot-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = document.getElementById('chat-query').value;
    const responseBox = document.getElementById('chatbot-response');
    responseBox.innerText = '⏳ جاري تحليل السؤال...';

    fetch(`${API_BASE}/chatbot/query`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('POST', '/api/chatbot/query', status, data);
        responseBox.innerHTML = `<strong>الرد السريري:</strong> ${data.message || data.response || 'لم يتم العثور على رد'}`;
    })
    .catch(() => { responseBox.innerText = '❌ فشل الاتصال بخادم الذكاء الاصطناعي'; });
});

// Upload Medical Records
document.getElementById('upload-record-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('medical-file');
    if (!fileInput.files[0]) {
        alert('اختر ملفاً أولاً!');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch(`${API_BASE}/files/upload-file`, {
        method: 'POST',
        headers: getAuthHeaders(), // لا نضيف Content-Type يدوياً — المتصفح يضيفه تلقائياً مع الـ boundary
        body: formData
    })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('POST', '/api/files/upload-file', status, data);
        if (status === 200 || status === 201) {
            alert(`✅ ${data.message}`);
            document.getElementById('upload-record-form').reset();
        } else {
            alert(`❌ ${data.detail || data.message || 'فشل رفع الملف'}`);
        }
    });
});


// Doctor Fetch Medical Records
function fetchMedicalRecords() {
    const input = document.getElementById('record-patient-id').value.trim();
    const endpoint = input ? `/records/${input}` : `/records/`;
    
    const responseBox = document.getElementById('medical-records-response');
    responseBox.style.display = 'block';
    responseBox.innerText = '⏳ جاري جلب السجلات الطبية...';

    fetch(`${API_BASE}${endpoint}`, { headers: getAuthHeaders() })
    .then(res => res.json().then(data => ({ status: res.status, data })))
    .then(({ status, data }) => {
        logApiCall('GET', `/api${endpoint}`, status, data);
        responseBox.innerHTML = `<pre style="margin:0; white-space:pre-wrap;">${JSON.stringify(data, null, 2)}</pre>`;
    });
}

