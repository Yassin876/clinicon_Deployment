import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ArrowRight, User } from 'lucide-react';
import { getDoctors, getAvailableSlots, book } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { getClinicMeta, getSpecName } from '../utils/clinics';
import { useLang } from '../context/LangContext';

export default function Book() {
  const { user } = useAuth();
  const toast = useToast();
  const { t, lang } = useLang();
  const location = useLocation();
  const nav = useNavigate();

  const [doctors, setDoctors] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(location.state?.doctor || null);
  const [selectedClinic, setSelectedClinic] = useState(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [name, setName] = useState(getDisplayName(user));
  const [phone, setPhone] = useState(user?.phone_number || user?.phone || '');
  const [step, setStep] = useState(selectedDoc ? 2 : 1);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [hoveredClinic, setHoveredClinic] = useState(null);

  useEffect(() => { getDoctors().then(setDoctors).catch(() => {}); }, []);

  useEffect(() => {
    if (selectedDoc && selectedDate) {
      setLoadingSlots(true);
      getAvailableSlots(selectedDoc.id, selectedDate)
        .then(res => {
          const slotList = res.slots || res.data || res || [];
          setSlots(slotList);
          if (slotList.length > 0) setSelectedSlot(slotList[0]);
          else setSelectedSlot(null);
        })
        .catch(() => setSlots([]))
        .finally(() => setLoadingSlots(false));
    }
  }, [selectedDoc, selectedDate]);

  const clinicGroups = {};
  doctors.forEach(doc => {
    const spec = doc.specialization;
    if (!clinicGroups[spec]) clinicGroups[spec] = [];
    clinicGroups[spec].push(doc);
  });

  const goConfirm = (e) => {
    e.preventDefault();
    if (!selectedSlot) { setError('يرجى اختيار موعد متاح'); return; }
    setError(''); setStep(3);
  };

  const handleBook = async () => {
    setLoading(true); setError('');
    try {
      const data = await book(selectedDoc?.id, selectedSlot, name.trim(), phone.trim());
      setResult(data.data || data); setStep(4);
      toast(t('bookingSuccessToast'), 'success');
    } catch (err) {
      const msg = err.message || err.error || t('bookingError');
      setError(msg); toast(msg, 'error');
    } finally { setLoading(false); }
  };

  const STEPS = [
    { n: 1, label: t('step1') },
    { n: 2, label: t('step2') },
    { n: 3, label: t('step3') },
  ];
  const activeStep = step <= 1 ? 1 : step === 2 ? 2 : 3;

  return (
    <div className="fade-up">
      {/* Full-width Progress Steps */}
      {step <= 3 && (
        <div className="booking-wizard">
          <div className="booking-steps-full">
            {STEPS.map((s, i) => {
              const isActive = s.n === activeStep;
              const isDone = s.n < activeStep;
              return (
                <div key={s.n} className={`wizard-step ${isActive ? 'active' : isDone ? 'done' : 'pending'}`}>
                  <div className="wizard-step-header">
                    {i > 0 && <div className={`wizard-line ${isDone ? 'done' : ''}`} />}
                    <div className={`step-circle ${isActive ? 'active' : isDone ? 'done' : 'pending'}`}>
                      {isDone ? '✓' : s.n}
                    </div>
                    {i < 2 && <div className={`wizard-line ${isDone || isActive ? 'done' : ''}`} />}
                  </div>
                  <div className="wizard-step-label">{s.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Step Content — Centered */}
      <div style={{ maxWidth: 740, margin: '0 auto' }}>
        {/* Step 1a: Choose Clinic */}
        {step === 1 && !selectedClinic && (
          <>
            <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, textAlign: 'center' }}>{t('chooseClinic')}</div>
            <div style={{ fontSize: 13.5, color: 'var(--text-muted)', marginBottom: 22, textAlign: 'center' }}>{t('whichSpec')}</div>
            <div className="book-clinic-grid">
              {Object.entries(clinicGroups).map(([spec, docs]) => {
                const cm = getClinicMeta(spec);
                const Icon = cm.icon;
                return (
                  <button key={spec} className="book-clinic-option" style={{ position: 'relative' }}
                    onClick={() => setSelectedClinic(spec)}
                    onMouseEnter={() => setHoveredClinic(spec)}
                    onMouseLeave={() => setHoveredClinic(null)}>
                    <div className="clinic-icon-circle" style={{ background: cm.tint, color: cm.ink, width: 46, height: 46 }}>
                      <Icon size={22} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 15.5, fontWeight: 700 }}>{lang === 'ar' ? `عيادة ${spec}` : `${getSpecName(spec, lang)} Clinic`}</div>
                      <div className="clinic-badge" style={{ marginTop: 4 }}>
                        {docs.length} {t('doctors')}
                      </div>
                    </div>
                    {hoveredClinic === spec && (
                      <div className="clinic-hover-desc">{lang === 'en' && cm.descEn ? cm.descEn : cm.desc}</div>
                    )}
                  </button>
                );
              })}
            </div>
          </>
        )}

        {/* Step 1b: Choose Doctor */}
        {step === 1 && selectedClinic && (
          <>
            <button className="back-btn" onClick={() => setSelectedClinic(null)} style={{ marginBottom: 16 }}>
              <ArrowRight size={14} style={{ transform: lang === 'en' ? 'scaleX(-1)' : 'none' }} /> {t('backToClinics')}
            </button>
            <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 6, textAlign: 'center' }}>
              {t('chooseDoctor')} {getSpecName(selectedClinic, lang)}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 18 }}>
              {(clinicGroups[selectedClinic] || []).map(doc => (
                <button key={doc.id} className="book-doctor-option"
                  onClick={() => { setSelectedDoc(doc); setStep(2); }}>
                  <div className="doc-avatar-placeholder" style={{ width: 46, height: 46 }}>
                    <User size={20} />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 15.5, fontWeight: 700 }}>{doc.name}</div>
                    <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 3 }}>{getSpecName(doc.specialization, lang)}</div>
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--text-faint)', flexShrink: 0 }}>
                    <span className="online-dot" style={{ width: 6, height: 6 }} /> {t('available')}
                  </div>
                </button>
              ))}
            </div>
          </>
        )}

        {/* Step 2: Patient Data */}
        {step === 2 && (
          <div className="sphg-card" style={{ padding: 28 }}>
            {/* Selected doctor summary */}
            <div style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              padding: 16, borderRadius: 12, background: 'var(--bg)', border: '1px solid var(--border-light)', marginBottom: 24,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div className="doc-avatar-placeholder" style={{ width: 42, height: 42 }}>
                  <User size={18} />
                </div>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700 }}>{selectedDoc?.name}</div>
                  <div style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>{getSpecName(selectedDoc?.specialization, lang)}</div>
                </div>
              </div>
              <button className="btn-secondary" style={{ padding: '6px 14px', fontSize: 12.5 }}
                onClick={() => { setStep(1); setSelectedClinic(null); }}>{t('change')}</button>
            </div>

            <form onSubmit={goConfirm}>
              <div className="book-form-grid" style={{ marginBottom: 18 }}>
                <div>
                  <label className="label">{t('patientName')}</label>
                  <input value={name} onChange={e => setName(e.target.value)} required
                    className="input-field" placeholder={lang === 'ar' ? 'مثال: سارة عبدالله' : 'e.g. Sarah Abdullah'} />
                </div>
                <div>
                  <label className="label">{t('mobile')}</label>
                  <input value={phone} onChange={e => setPhone(e.target.value)} required
                    className="input-field" placeholder="01012345678"
                    style={{ direction: 'ltr', textAlign: lang === 'ar' ? 'right' : 'left', fontFamily: 'var(--font-mono)' }} />
                </div>
              </div>

              <div style={{ marginBottom: 18 }}>
                <label className="label">اختر تاريخ الموعد</label>
                <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]} className="input-field" style={{ borderRadius: 10, padding: '11px 14px' }} required />
              </div>

              <div style={{ marginBottom: 18 }}>
                <label className="label">المواعيد المتاحة</label>
                {loadingSlots ? (
                  <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>جاري تحميل المواعيد...</div>
                ) : slots.length === 0 ? (
                  <div style={{ fontSize: 13, color: 'var(--danger)' }}>لا توجد مواعيد متاحة في هذا اليوم</div>
                ) : (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))', gap: 8, marginTop: 8 }}>
                    {slots.map(s => {
                      const timeStr = new Date(s).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                      const isSel = selectedSlot === s;
                      return (
                        <button type="button" key={s} onClick={() => setSelectedSlot(s)}
                          style={{
                            padding: '8px 10px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                            border: isSel ? '2px solid var(--primary)' : '1px solid var(--border)',
                            background: isSel ? 'var(--primary-tint)' : 'var(--card)',
                            color: isSel ? 'var(--primary)' : 'var(--text)', cursor: 'pointer',
                          }}>
                          {timeStr}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
              <button type="submit" disabled={!selectedSlot} className="btn-primary" style={{ width: '100%', marginTop: 24, padding: 14 }}>
                {t('next')}
              </button>
            </form>
          </div>
        )}

        {/* Step 3: Confirm */}
        {step === 3 && (
          <div className="sphg-card" style={{ padding: 28 }}>
            <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 22, textAlign: 'center' }}>{t('confirmBooking')}</div>
            <div className="booking-summary">
              {[
                [t('clinicLabel'), getSpecName(selectedDoc?.specialization, lang)],
                [t('doctorLabel'), selectedDoc?.name],
                [t('nameLabel'), name],
                [t('mobileLabel'), phone],
                ['تاريخ الموعد', selectedDate],
                ['وقت الموعد', selectedSlot ? new Date(selectedSlot).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'],
                ['حالة الموعد', 'في الانتظار'],
              ].map(([k, v]) => (
                <div key={k} className="booking-summary-row">
                  <div style={{ fontSize: 13, color: 'var(--text-faint)', fontWeight: 600 }}>{k}</div>
                  <div style={{ fontSize: 14.5, fontWeight: 600 }}>{v}</div>
                </div>
              ))}
            </div>
            {error && <div className="error-box" style={{ marginTop: 16 }}>{error}</div>}
            <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'center' }}>
              <button onClick={handleBook} disabled={loading} className="btn-primary" style={{ padding: '13px 32px', fontSize: 14.5 }}>
                {loading ? t('confirming') : t('confirmBooking')}
              </button>
              <button onClick={() => setStep(2)} className="btn-secondary">{t('back')}</button>
            </div>
          </div>
        )}

        {/* Step 4: Success */}
        {step === 4 && result && (
          <div className="booking-success">
            <div className="booking-success-icon">✓</div>
            <div style={{ fontSize: 23, fontWeight: 700, marginTop: 20 }}>{t('bookingConfirmed')}</div>
            <div style={{ fontSize: 14.5, color: 'var(--text-muted)', marginTop: 8 }}>
              {selectedDoc?.name} · {getSpecName(selectedDoc?.specialization, lang)}
            </div>

            <div className="booking-success-cards" style={{ marginTop: 20 }}>
              <div style={{ background: 'var(--deep)', color: '#EAF2F0', borderRadius: 16, padding: 22, textAlign: 'center' }}>
                <div style={{ fontSize: 12.5, color: 'rgba(234,242,240,0.65)', fontWeight: 600 }}>حالة الموعد</div>
                <div style={{ fontSize: 28, fontWeight: 700, marginTop: 10, color: '#EAF2F0' }}>
                  في الانتظار
                </div>
              </div>
              <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 16, padding: 22, textAlign: 'center' }}>
                <div style={{ fontSize: 12.5, color: 'var(--text-faint)', fontWeight: 600 }}>الوقت المحدد لك</div>
                <div style={{ fontSize: 32, fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: 6, color: 'var(--primary)' }}>
                  {result.appointmentTime || (selectedSlot ? new Date(selectedSlot).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—')}
                </div>
                <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 6 }}>{result.bookingDate || selectedDate}</div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 28 }}>
              <button onClick={() => nav('/queue', { state: { booking: result } })}
                className="btn-primary" style={{ padding: '13px 24px', fontSize: 14.5 }}>
                {t('goToQueue')}
              </button>
              <button onClick={() => { setStep(1); setSelectedClinic(null); setSelectedDoc(null); setResult(null); }}
                className="btn-secondary">{t('newBooking')}</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getDisplayName(user) {
  // اسم المريض يجب أن يكون اسم شخصي فقط - لا نستخدم اسم العيادة أو المختبر
  const raw = user?.name || user?.full_name || '';
  
  // إذا كان المستخدم clinic_owner أو lab - لا نستخدم full_name لأنه اسم العيادة/المختبر
  if (user?.role === 'clinic_owner' || user?.role === 'lab') {
    return '';
  }
  
  // لو المستخدم دكتور - لا نستخدم اسمه لأن الدكتور لا يعمل booking
  if (user?.role === 'doctor') {
    return '';
  }
  
  if (!raw || raw.includes('@') || /^[a-zA-Z0-9._-]+$/.test(raw)) return '';
  return raw;
}
