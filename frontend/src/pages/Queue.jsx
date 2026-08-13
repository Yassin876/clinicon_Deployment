import { useEffect, useState, useCallback, useMemo } from 'react';
import { useLocation } from 'react-router-dom';
import { Clock, CheckCircle, Pill, FileText } from 'lucide-react';
import {
  getQueue, markDone, prescribeMedication, createPatientNote,
  getPatientNotes, getPatientVisits, getPatientMedications, getPatientFiles, endDoctorTodayLeave,
} from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LangContext';
import { useToast } from '../context/ToastContext';

export default function Queue() {
  const { t, lang } = useLang();
  const { user } = useAuth();
  const toast = useToast();
  const myBooking = useLocation().state?.booking;
  const [queue, setQueue] = useState([]);
  const [loading, setLoading] = useState(true);
  const [secs, setSecs] = useState(10);
  const [prescribeModal, setPrescribeModal] = useState(null);
  const [prescribeForm, setPrescribeForm] = useState({ medicine_name: '', dosage: '', frequency: '' });
  const [prescribeSaving, setPrescribeSaving] = useState(false);
  const [patientMeds, setPatientMeds] = useState([]);
  const [notesModal, setNotesModal] = useState(null);
  const [notes, setNotes] = useState([]);
  const [patientVisits, setPatientVisits] = useState([]);
  const [newNote, setNewNote] = useState('');

  const isPatient = user?.role === 'patient';
  const isClinicOwner = user?.role === 'clinic_owner';
  const isDoctor = user?.role === 'doctor';

  const [ownerStats, setOwnerStats] = useState(null);

  const fetchQueue = useCallback(() => {
    getQueue().then(r => {
      const resData = r.data || r;
      if (resData && typeof resData === 'object' && !Array.isArray(resData)) {
        setOwnerStats(resData);
        setQueue([]);
      } else {
        setQueue(Array.isArray(resData) ? resData : []);
        setOwnerStats(null);
      }
    })
      .catch(() => { }).finally(() => setLoading(false));
  }, []);

  // Doctor-specific actions
  const markPatientDone = async (appointmentId) => {
    try {
      const result = await markDone(appointmentId);
      if (result.success) {
        toast(result.message, 'success');
        fetchQueue();
      } else {
        toast(result.message || 'خطأ في تحديث الحالة', 'error');
      }
    } catch (error) {
      toast(error.message || 'حدث خطأ', 'error');
    }
  };

  const openPrescribe = async (patient) => {
    setPrescribeModal({ patient_id: patient.patient_id, name: patient.name });
    setPrescribeForm({ medicine_name: '', dosage: '', frequency: '' });
    try {
      const m = await getPatientMedications(patient.patient_id);
      setPatientMeds(Array.isArray(m) ? m : m.data || []);
    } catch {
      setPatientMeds([]);
    }
  };

  const handlePrescribe = async (e) => {
    e.preventDefault();
    if (!prescribeForm.medicine_name.trim()) return;
    setPrescribeSaving(true);
    try {
      await prescribeMedication({
        patient_id: prescribeModal.patient_id,
        medicine_name: prescribeForm.medicine_name,
        dosage: prescribeForm.dosage,
        frequency: prescribeForm.frequency,
      });
      setPrescribeForm({ medicine_name: '', dosage: '', frequency: '' });
      const m = await getPatientMedications(prescribeModal.patient_id);
      setPatientMeds(Array.isArray(m) ? m : m.data || []);
      toast(t('medPrescribed'), 'success');
    } catch {
      toast(t('errorOccurred'), 'error');
    } finally {
      setPrescribeSaving(false);
    }
  };

  const [patientFiles, setPatientFiles] = useState([]);

  const openPatientNotes = async (patient) => {
    setNotesModal({ patient_id: patient.patient_id, doctor_id: patient.doctor_id, name: patient.name });
    setNewNote('');
    try {
      const [n, v, f] = await Promise.all([
        getPatientNotes(patient.patient_id).catch(() => []),
        getPatientVisits(patient.patient_id).catch(() => []),
        getPatientFiles(patient.patient_id).catch(() => []),
      ]);
      setNotes(n.data || n || []);
      setPatientVisits(v.data || v || []);
      setPatientFiles(f.data || f || []);
    } catch {
      setNotes([]);
      setPatientVisits([]);
      setPatientFiles([]);
    }
  };

  const handleAddNote = async (e) => {
    e.preventDefault();
    if (!newNote.trim()) return;
    try {
      await createPatientNote({
        patient_id: notesModal.patient_id,
        doctor_id: notesModal.doctor_id,
        note: newNote,
      });
      setNewNote('');
      const n = await getPatientNotes(notesModal.patient_id).catch(() => []);
      setNotes(n.data || n || []);
      toast(t('noteSaved'), 'success');
    } catch {
      toast(t('errorOccurred'), 'error');
    }
  };

  useEffect(() => {
    fetchQueue();
    const id = setInterval(() => {
      setSecs(prev => {
        if (prev <= 1) { fetchQueue(); return 10; }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [fetchQueue]);

  // Find the patient's own entry by phone (from booking) or name
  const myPhone = myBooking?.phone || user?.phone_number || user?.phone;
  const myName = user?.full_name || user?.name;
  const myBookingId = myBooking?.id || null;
  const myPatientId = myBooking?.patient_id || null;
  const myDoctorId = myBooking?.doctor_id || null;

  const myEntry = useMemo(() => {
    if (!isPatient) return null;
    if (myBookingId) {
      const byBookingId = queue.find(p => p.id === myBookingId || p.patient_id === myPatientId);
      if (byBookingId) return byBookingId;
    }
    if (myPhone) {
      const byPhone = queue.find(p => p.phone === myPhone);
      if (byPhone) return byPhone;
    }
    if (myName) {
      const byName = queue.find(p => p.name === myName);
      if (byName) return byName;
    }
    return null;
  }, [queue, myBookingId, myPatientId, myPhone, myName, isPatient]);

  // Scope the queue based on the logged-in role
  const filteredQueue = useMemo(() => {
    let list = queue;
    if (isClinicOwner) list = queue;
    else if (isDoctor) list = queue.filter(p => p.doctor_id === user?.doctor_id);
    else if (myEntry?.doctor_id || myDoctorId) {
      const doctorIdToShow = myEntry?.doctor_id || myDoctorId;
      list = queue.filter(p => p.doctor_id === doctorIdToShow);
    } else if (isPatient && myEntry) {
      list = queue.filter(p => p.doctor_id === myEntry.doctor_id);
    }
    return [...list].sort((a, b) => a.queueNumber - b.queueNumber);
  }, [queue, myEntry, isPatient, isClinicOwner, isDoctor, user, myDoctorId]);

  const waiting = filteredQueue.filter(q => q.status === 'waiting');
  const current = filteredQueue.find(q => q.isCurrent);
  const isMe = (p) => myEntry && p.id === myEntry.id;
  const ahead = myEntry ? waiting.filter(q => q.queueNumber < myEntry.queueNumber && q.status === 'waiting').length : 0;

  const statusLabel = (p) => {
    if (p.isCurrent) return { text: t('inClinic'), bg: 'var(--primary-light)', fg: 'var(--primary)' };
    if (p.status === 'done') return { text: t('doneStatus'), bg: 'var(--bg-alt)', fg: 'var(--text-muted)' };
    return { text: t('inWaiting'), bg: 'var(--bg-alt)', fg: 'var(--text-secondary)' };
  };

  return (
    <div className="fade-up" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Doctor banner / Action header */}
      {isDoctor && (
        <div style={{
          background: 'var(--primary-light)', borderRadius: 12, padding: '12px 20px',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10
        }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--primary)' }}>
            لوحة تحكم الطبيب - قائمة الانتظار والمواعيد
          </span>
          <button
            onClick={async () => {
              if (window.confirm('هل أنت تأكد من إنهاء عمل اليوم؟ سيتم الاعتذار لجميع المرضى المتبقين وإرسال إشعارات لهم.')) {
                try {
                  const res = await endDoctorTodayLeave();
                  fetchQueue();
                  alert(res.message || 'تم إنهاء عمل اليوم بنجاح');
                } catch (err) {
                  alert(err.message || 'حدث خطأ أثناء إنهاء عمل اليوم');
                }
              }
            }}
            style={{
              padding: '8px 16px', fontSize: 13, fontWeight: 700, borderRadius: 8,
              border: 'none', background: '#dc2626', color: 'white', cursor: 'pointer'
            }}
          >
            🚫 إنهاء عمل اليوم واعتذار المتبقين
          </button>
        </div>
      )}

      {/* Doctor name banner for patient */}
      {isPatient && myEntry && (
        <div style={{
          background: 'var(--primary-light)', borderRadius: 12, padding: '12px 20px',
          fontSize: 14, fontWeight: 600, color: 'var(--primary)', textAlign: 'center',
        }}>
          {t('queueFor')} {myEntry.doctor}
        </div>
      )}

      {/* Stats Row */}
      {isClinicOwner && ownerStats ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="queue-stats">
            <div className="stat-card dark">
              <div className="stat-card-label">إجمالي المرضى اليوم</div>
              <div className="stat-card-value" style={{ fontSize: 40 }}>{ownerStats.totalPatients ?? 0}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">في الانتظار</div>
              <div className="stat-card-value" style={{ fontSize: 40 }}>{ownerStats.waitingPatients ?? 0}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">تم الانتهاء</div>
              <div className="stat-card-value" style={{ fontSize: 40 }}>{ownerStats.completedPatients ?? 0}</div>
            </div>
          </div>

          {/* Per-Doctor Breakdown Cards for Clinic Owner */}
          {ownerStats.doctorStats && ownerStats.doctorStats.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: 'var(--text)' }}>
                👨‍⚕️ تفاصيل أطباء العيادة ومواعيد عمل اليوم
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
                {ownerStats.doctorStats.map((doc, idx) => (
                  <div key={doc.doctor_id || idx} className="sphg-card" style={{ padding: 18, border: '1px solid var(--border-light)', borderRadius: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--primary)' }}>{doc.doctor_name}</span>
                      <span style={{ fontSize: 11, background: 'var(--bg-alt)', padding: '2px 8px', borderRadius: 6, color: 'var(--text-muted)' }}>
                        {doc.specialization || 'طبيب'}
                      </span>
                    </div>
                    
                    <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Clock size={14} color="var(--primary)" />
                      <span>ساعات العمل اليوم: <strong>{doc.work_hours}</strong></span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, background: 'var(--bg-alt)', padding: 10, borderRadius: 8, textAlign: 'center' }}>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>الإجمالي</div>
                        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text)' }}>{doc.total}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>في الانتظار</div>
                        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--warning, #d97706)' }}>{doc.pending}</div>
                      </div>
                      <div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>تم الكشف</div>
                        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--success, #16a34a)' }}>{doc.completed}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="queue-stats">
          <div className="stat-card dark">
            <div className="stat-card-label">{t('servingNow')}</div>
            <div className="stat-card-value" style={{ fontSize: 40 }}>{current?.queueNumber || '—'}</div>
            <div className="stat-card-sub">{current?.name || '—'}</div>
          </div>
          <div className="stat-card">
            <div className="stat-card-label">{t('waiting')}</div>
            <div className="stat-card-value" style={{ fontSize: 40 }}>{waiting.length}</div>
            <div className="stat-card-sub">{waiting.length > 0 ? `~${Math.round(waiting.length * (queue[0]?.avgServiceMin || 15))} ${t('minuteWord')}` : '—'}</div>
          </div>
          <div className="stat-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="online-dot" />
              <div className="stat-card-label">{t('liveUpdate')}</div>
            </div>
            <div style={{ fontSize: 15, fontWeight: 600, marginTop: 12 }}>
              {t('refreshIn')} {secs} {t('seconds')}
            </div>
            <div className="refresh-bar">
              <div className="refresh-bar-fill" style={{ width: `${(secs / 10) * 100}%` }} />
            </div>
            <button onClick={() => { fetchQueue(); setSecs(10); }}
              style={{
                marginTop: 12, border: 'none', background: 'transparent', padding: 0,
                cursor: 'pointer', color: 'var(--primary)', fontSize: 13, fontWeight: 600,
                textDecoration: 'underline', fontFamily: 'inherit',
              }}>{t('refreshNow')}</button>
          </div>
        </div>
      )}

      {/* Doctor: Current patient actions */}
      {isDoctor && current && current.status !== 'done' && (
        <div className="queue-my-card" style={{ border: '2px solid var(--primary)', background: 'var(--primary-tint)' }}>
          <div className="queue-my-ring">
            <div style={{ fontSize: 21, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--primary)' }}>
              {current.queueNumber}
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 16.5, fontWeight: 700, color: 'var(--text)' }}>
              {t('inClinic')}: {current.name}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>{current.phone}</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
              <button
                onClick={() => markPatientDone(current.id)}
                style={{
                  padding: '8px 16px', fontSize: 13, fontWeight: 600, borderRadius: 6,
                  border: 'none', background: 'var(--success)', color: 'white', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 6,
                }}
              >
                <CheckCircle size={15} /> تم الكشف
              </button>
              <button
                onClick={() => openPrescribe(current)}
                style={{
                  padding: '8px 16px', fontSize: 13, fontWeight: 600, borderRadius: 6,
                  border: '1px solid var(--primary)', background: 'white', color: 'var(--primary)', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 6,
                }}
              >
                <Pill size={15} /> إضافة دواء
              </button>
              <button
                onClick={() => openPatientNotes(current)}
                style={{
                  padding: '8px 16px', fontSize: 13, fontWeight: 600, borderRadius: 6,
                  border: '1px solid var(--info)', background: 'white', color: 'var(--info)', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 6,
                }}
              >
                <FileText size={15} /> كتابة ملاحظات
              </button>
            </div>
          </div>
        </div>
      )}

      {/* My Position */}
      {myEntry && myEntry.status === 'waiting' && (
        <div className="queue-my-card">
          <div className="queue-my-ring">
            <div style={{ fontSize: 21, fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--primary)' }}>
              {myEntry.queueNumber}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 16.5, fontWeight: 700, color: 'var(--text)' }}>{t('yourBooking')}</div>
            <div style={{ fontSize: 13.5, color: 'var(--text-muted)', marginTop: 5, lineHeight: 1.6 }}>
              {t('aheadOfYou')} {ahead} {t('patientsAhead')} · {t('expectedWait')} {Math.round(ahead * (myEntry.avgServiceMin || 15))} {t('minuteWord')}
            </div>
          </div>
        </div>
      )}

      {/* Queue Table / Doctor's Patient List */}
      {loading ? (
        <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>{t('loading')}</div>
      ) : filteredQueue.length === 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, padding: 48 }}>
          <Clock size={28} color="var(--text-muted)" />
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{t('emptyQueue')}</p>
        </div>
      ) : isDoctor ? (
        /* Doctor View: Same professional queue table with action buttons */
        <div className="queue-table">
          <div className="queue-table-header">
            <div>{t('number')}</div>
            <div>{t('patient')}</div>
            <div>{t('status')}</div>
            <div style={{ textAlign: 'center' }}>الإجراءات</div>
          </div>
          {filteredQueue.map((p, i) => {
            const st = statusLabel(p);
            return (
              <div key={p.id || i} className="queue-table-row" style={{
                background: p.isCurrent ? 'var(--bg)' : 'var(--card)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}>
                <div style={{
                  fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)',
                  color: p.status === 'done' ? 'var(--text-muted)' : (p.isCurrent ? 'var(--primary)' : 'var(--text)'),
                  width: '12%',
                }}>{p.queueNumber}</div>
                <div style={{ fontSize: 14.5, fontWeight: 500, width: '25%' }}>
                  <div>{p.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{p.phone}</div>
                </div>
                <div style={{ width: '20%' }}>
                  <span className="queue-badge" style={{ background: st.bg, color: st.fg }}>
                    <span className="badge-dot" style={{ background: st.fg }} />
                    {st.text}
                  </span>
                </div>
                <div style={{ width: '43%', display: 'flex', gap: 6, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
                  {p.status !== 'done' ? (
                    <>
                      <button
                        onClick={() => markPatientDone(p.id)}
                        style={{
                          padding: '6px 12px', fontSize: 11, fontWeight: 600, borderRadius: 4,
                          border: 'none', background: 'var(--success)', color: 'white', cursor: 'pointer',
                        }}
                      >
                        تم الكشف
                      </button>
                      <button
                        onClick={() => openPrescribe(p)}
                        style={{
                          padding: '6px 12px', fontSize: 11, fontWeight: 600, borderRadius: 4,
                          border: '1px solid var(--primary)', background: 'transparent', color: 'var(--primary)', cursor: 'pointer',
                        }}
                      >
                        دواء
                      </button>
                      <button
                        onClick={() => openPatientNotes(p)}
                        style={{
                          padding: '6px 12px', fontSize: 11, fontWeight: 600, borderRadius: 4,
                          border: '1px solid var(--info)', background: 'transparent', color: 'var(--info)', cursor: 'pointer',
                        }}
                      >
                        ملاحظات
                      </button>
                    </>
                  ) : (
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>تم الكشف</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Patient/Clinic Owner View: Queue Table */
        <div className="queue-table">
          <div className="queue-table-header">
            <div>{t('number')}</div>
            <div>{t('patient')}</div>
            {!isPatient && <div>{t('doctor')}</div>}
            <div>{t('status')}</div>
          </div>
          {filteredQueue.map((p, i) => {
            const st = statusLabel(p);
            const mine = isMe(p);
            return (
              <div key={p.id || i} className="queue-table-row" style={{
                background: mine ? 'var(--primary-tint)' : (p.isCurrent ? 'var(--bg)' : 'var(--card)'),
              }}>
                <div style={{
                  fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-mono)',
                  color: p.status === 'done' ? 'var(--text-muted)' : (mine || p.isCurrent ? 'var(--primary)' : 'var(--text)'),
                }}>{p.queueNumber}</div>
                <div style={{ fontSize: 14.5, fontWeight: mine ? 700 : 500, display: 'flex', alignItems: 'center', gap: 8 }}>
                  {p.name}
                  {mine && <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--primary)' }}>({t('you')})</span>}
                </div>
                {!isPatient && <div style={{ fontSize: 13.5, color: 'var(--text-muted)' }}>{p.doctor || '—'}</div>}
                <div>
                  <span className="queue-badge" style={{ background: st.bg, color: st.fg }}>
                    <span className="badge-dot" style={{ background: st.fg }} />
                    {st.text}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Prescribe Medication Modal */}
      {prescribeModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'grid', placeItems: 'center', zIndex: 999 }}
          onClick={() => setPrescribeModal(null)}>
          <div className="sphg-card" style={{ padding: 26, width: '90%', maxWidth: 440 }} onClick={e => e.stopPropagation()}>
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>{t('prescribeMed')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>{prescribeModal.name}</div>
            <form onSubmit={handlePrescribe} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input value={prescribeForm.medicine_name} onChange={e => setPrescribeForm({ ...prescribeForm, medicine_name: e.target.value })}
                placeholder={t('medName')} className="input-field" style={{ borderRadius: 10, padding: '11px 14px' }} required />
              <input value={prescribeForm.dosage} onChange={e => setPrescribeForm({ ...prescribeForm, dosage: e.target.value })}
                placeholder={t('dosage')} className="input-field" style={{ borderRadius: 10, padding: '11px 14px' }} />
              <input value={prescribeForm.frequency} onChange={e => setPrescribeForm({ ...prescribeForm, frequency: e.target.value.replace(/[^0-9]/g, '') })}
                placeholder={t('frequencyNum')} className="input-field" type="number" min="1" max="10"
                style={{ borderRadius: 10, padding: '11px 14px' }} />
              <button type="submit" disabled={prescribeSaving} className="btn-primary" style={{ padding: 12 }}>
                {prescribeSaving ? t('saving') : t('prescribeAdd')}
              </button>
            </form>
            {patientMeds.length > 0 && (
              <div style={{ marginTop: 18 }}>
                <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text-faint)', marginBottom: 8 }}>{t('currentMeds')}</div>
                {patientMeds.map((m) => (
                  <div key={m.id} style={{
                    padding: '8px 12px', background: 'var(--card)', border: '1px solid var(--border-light)',
                    borderRadius: 8, marginBottom: 6, fontSize: 13,
                  }}>
                    💊 {m.medicine_name}
                    {m.dosage && <span style={{ color: 'var(--text-muted)' }}> — {m.dosage}</span>}
                    {m.frequency && <span style={{ color: 'var(--primary)', fontSize: 11.5 }}> ({m.frequency}x)</span>}
                  </div>
                ))}
              </div>
            )}
            <button className="btn-secondary" style={{ marginTop: 14, width: '100%' }} onClick={() => setPrescribeModal(null)}>{t('back')}</button>
          </div>
        </div>
      )}

      {/* Patient Notes Modal */}
      {notesModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', display: 'grid', placeItems: 'center', zIndex: 999 }}
          onClick={() => setNotesModal(null)}>
          <div className="sphg-card" style={{ padding: 28, width: '92%', maxWidth: 520, maxHeight: '80vh', overflow: 'auto' }} onClick={e => e.stopPropagation()}>
            <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>{t('patientNotes')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginBottom: 20 }}>{notesModal.name}</div>
            <form onSubmit={handleAddNote} style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
              <input value={newNote} onChange={e => setNewNote(e.target.value)}
                placeholder={t('noteText')} className="input-field" style={{ flex: 1 }} />
              <button type="submit" className="btn-primary" style={{ padding: '10px 16px', fontSize: 13 }}>{t('addNote')}</button>
            </form>
            {notes.length > 0 && notes.map((n, i) => (
              <div key={n.id || i} style={{ padding: '10px 14px', borderRadius: 10, background: 'var(--bg-alt)', marginBottom: 8, fontSize: 13.5 }}>
                {n.note}
                <div style={{ fontSize: 11, color: 'var(--text-faint)', marginTop: 4 }}>
                  {n.created_at ? new Date(n.created_at).toLocaleString(lang === 'ar' ? 'ar-EG' : 'en-US') : ''}
                </div>
              </div>
            ))}
            {patientVisits.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-faint)', marginBottom: 10 }}>{t('visits')}</div>
                {patientVisits.map((v, i) => (
                  <div key={v.id || i} style={{ padding: '12px 14px', borderRadius: 10, border: '1px solid var(--border-light)', marginBottom: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ fontWeight: 600 }}>{v.diagnosis || '—'}</span>
                      <span style={{ color: 'var(--text-faint)', fontSize: 12 }}>{v.visit_date}</span>
                    </div>
                    {v.doctor_notes && <div style={{ fontSize: 12, color: 'var(--text-faint)', marginTop: 4 }}>{v.doctor_notes}</div>}
                  </div>
                ))}
              </div>
            )}
            {patientFiles.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-faint)', marginBottom: 10 }}>📁 الملفات والتحاليل المرفوعة</div>
                {patientFiles.map((f, i) => (
                  <div key={f.id || i} style={{ padding: '10px 14px', borderRadius: 10, border: '1px solid var(--border-light)', marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, overflow: 'hidden' }}>
                      <FileText size={16} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                      <span style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.file_name || f.filename}</span>
                    </div>
                    {f.id && (
                      <a href={`http://localhost:5000/api/files/download/${f.id}`} target="_blank" rel="noreferrer" style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 700, textDecoration: 'none', flexShrink: 0 }}>
                        تحميل / عرض
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
            {notes.length === 0 && patientVisits.length === 0 && patientFiles.length === 0 && (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, padding: 20 }}>{t('noNotes')}</div>
            )}
            <button className="btn-secondary" style={{ marginTop: 14, width: '100%' }} onClick={() => setNotesModal(null)}>{t('back')}</button>
          </div>
        </div>
      )}
    </div>
  );
}
