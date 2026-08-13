/**
 * api.js — كل طلبات الـ backend في مكان واحد.
 * Vite proxy بيحوّل /api/* → localhost:5000
 */
const BASE = import.meta.env?.VITE_API_URL || import.meta.env?.NEXT_PUBLIC_API_URL || '/api';

async function request(method, path, body = null) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE}${path}`, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, ...data };
  return data;
}

// Auth
export const login = (email, password) =>
  request('POST', '/auth/login', { email, password });

export const register = (full_name, email, password, role = 'patient', extra = {}) =>
  request('POST', '/auth/register', { full_name, email, password, role, ...extra });

// Doctors
export const getDoctors = () =>
  request('GET', '/doctors').then(r => r.data || r);

export const getAvailableSlots = (doctor_id, date) =>
  request('GET', `/doctors/${doctor_id}/available-slots?date=${date}`);

export const endDoctorTodayLeave = (reason = '') =>
  request('POST', '/doctors/leave/end-today', { reason });

// Booking (queue)
export const book = (doctor_id, slot_datetime, patient_name = '', patient_phone = '') =>
  request('POST', '/book', { doctor_id, slot_datetime, patient_name, patient_phone });

// Queue / Stats
export const getQueue = () => request('GET', '/queue');
export const getStats = () => request('GET', '/stats');
export const markDone = (id) => request('PUT', `/patient/${id}/done`);

// Medications
export const getMedications = () =>
  request('GET', '/medications/').then(r => r.data || r);
export const addMedication = (name, dosage, frequency) =>
  request('POST', '/medications/', { name, dosage, frequency });
export const deleteMedication = (id) =>
  request('DELETE', `/medications/${id}`);

// Files
export const uploadFile = async (file) => {
  const token = localStorage.getItem('token');
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/files/upload-file`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  return res.json();
};

export const searchPatients = (query) =>
  request('GET', `/files/search-patients?query=${encodeURIComponent(query)}`);

export const labUploadFile = async (patientIdentifier, testName, file) => {
  const token = localStorage.getItem('token');
  const form = new FormData();
  form.append('patient_identifier', patientIdentifier);
  if (testName) form.append('test_name', testName);
  form.append('file', file);

  const res = await fetch(`${BASE}/files/lab-upload`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw { status: res.status, ...data };
  return data;
};

// Visits
export const getVisits = () =>
  request('GET', '/visits/my');
export const createVisit = (data) =>
  request('POST', '/visits/', data);
export const getPatientVisits = (patientId) =>
  request('GET', `/visits/patient/${patientId}`);
export const updateVisit = (visitId, data) =>
  request('PUT', `/visits/${visitId}`, data);

// Patient Notes
export const createPatientNote = (data) =>
  request('POST', '/patient-notes/', data);
export const getPatientNotes = (patientId) =>
  request('GET', `/patient-notes/patient/${patientId}`);

// Medication extras
export const updateMedication = (id, data) =>
  request('PUT', `/medications/${id}`, data);
export const addMedReminders = (medicationId, reminders) =>
  request('POST', `/medications/${medicationId}/reminders`, reminders);

// Files listing
export const getMyFiles = () =>
  request('GET', '/files/my');
export const getPatientFiles = (patientId) =>
  request('GET', `/files/patient/${patientId}`);

// Telegram link
export const linkTelegram = (telegram_chat_id, telegram_notif_enabled = true) =>
  request('POST', '/medications/telegram-link', { telegram_chat_id, telegram_notif_enabled });
export const getTelegramStatus = () =>
  request('GET', '/medications/telegram-status');
export const getTelegramLinkUrl = () =>
  request('GET', '/medications/telegram-link-url');
export const prescribeMedication = (data) =>
  request('POST', '/medications/prescribe', data);
export const getPatientMedications = (patientId) =>
  request('GET', `/medications/patient/${patientId}`);
export const doctorUpdateMedication = (medId, data) =>
  request('PUT', `/medications/doctor/${medId}`, data);
export const doctorDeleteMedication = (medId) =>
  request('DELETE', `/medications/doctor/${medId}`);

export const chatbotQuery = (query) =>
  request('POST', '/chatbot/query', { query });

// Doctor Leave
export const createDoctorLeave = (payload) =>
  request('POST', '/doctors/leave', payload);

// Clinic Owner
export const registerClinic = (data) =>
  request('POST', '/clinic/register', data);
export const updateClinic = (data) =>
  request('PUT', '/clinic/update', data);
export const getMyClinic = () =>
  request('GET', '/clinic/my-clinic');
export const inviteDoctor = (data) =>
  request('POST', '/clinic/invite-doctor', data);
export const getMyClinicDoctors = () =>
  request('GET', '/clinic/my-doctors');
export const addClinicMember = (data) =>
  request('POST', '/clinic/add-member', data);
export const getMyLabs = () =>
  request('GET', '/clinic/my-labs');
export const getPendingClinicRequests = () =>
  request('GET', '/clinic/pending-requests');
export const approveClinicRequest = (userId) =>
  request('POST', `/clinic/approve-request/${userId}`);
export const rejectClinicRequest = (userId) =>
  request('POST', `/clinic/reject-request/${userId}`);
