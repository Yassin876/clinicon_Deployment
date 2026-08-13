import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, User, Building2, FlaskConical } from 'lucide-react';
import { register } from '../utils/api';
import { useLang } from '../context/LangContext';

const DAYS = [
  { id: 5, labelAr: 'السبت', labelEn: 'Sat' },
  { id: 6, labelAr: 'الأحد', labelEn: 'Sun' },
  { id: 0, labelAr: 'الإثنين', labelEn: 'Mon' },
  { id: 1, labelAr: 'الثلاثاء', labelEn: 'Tue' },
  { id: 2, labelAr: 'الأربعاء', labelEn: 'Wed' },
  { id: 3, labelAr: 'الخميس', labelEn: 'Thu' },
  { id: 4, labelAr: 'الجمعة', labelEn: 'Fri' },
];

export default function Register() {
  const { t, lang } = useLang();
  const [role, setRole] = useState(null); // null = picker screen, 'patient', 'doctor', 'lab'
  const [form, setForm] = useState({ full_name: '', email: '', password: '', phone_number: '', address: '', specialization: '', location_url: '', clinic_email: '' });
  const [daySchedules, setDaySchedules] = useState({
    5: { active: true, start_time: '09:00', end_time: '17:00' },
    6: { active: true, start_time: '09:00', end_time: '17:00' },
    0: { active: true, start_time: '09:00', end_time: '17:00' },
    1: { active: true, start_time: '09:00', end_time: '17:00' },
    2: { active: true, start_time: '09:00', end_time: '17:00' },
    3: { active: true, start_time: '09:00', end_time: '17:00' },
    4: { active: false, start_time: '09:00', end_time: '17:00' },
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const nav = useNavigate();
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const toggleDayActive = (id) => {
    setDaySchedules(prev => ({
      ...prev,
      [id]: { ...prev[id], active: !prev[id].active }
    }));
  };

  const updateDayTime = (id, field, value) => {
    setDaySchedules(prev => ({
      ...prev,
      [id]: { ...prev[id], [field]: value }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);

    // Client-side password validation
    const pw = form.password;
    if (pw.length < 8) {
      setError(lang === 'ar' ? 'كلمة المرور يجب ألا تقل عن 8 أحرف' : 'Password must be at least 8 characters');
      setLoading(false); return;
    }
    if (!/[a-zA-Z؀-ۿ]/.test(pw)) {
      setError(lang === 'ar' ? 'كلمة المرور لازم تحتوي على حرف واحد على الأقل (عربي أو إنجليزي)' : 'Password must contain at least one letter');
      setLoading(false); return;
    }
    if (!/\d/.test(pw)) {
      setError(lang === 'ar' ? 'كلمة المرور لازم تحتوي على رقم واحد على الأقل' : 'Password must contain at least one number');
      setLoading(false); return;
    }

    const extra = {
      clinic_email: form.clinic_email?.trim() || undefined,
      phone_number: form.phone_number,
      address: form.address,
      location_url: form.location_url,
      specialization: form.specialization || (role === 'doctor' ? 'عام' : undefined),
      availabilities: role === 'doctor' ? DAYS
        .filter(d => daySchedules[d.id]?.active)
        .map(d => ({
          day_of_week: d.id,
          start_time: daySchedules[d.id].start_time,
          end_time: daySchedules[d.id].end_time
        })) : undefined
    };

    try {
      await register(form.full_name, form.email, form.password, role, extra);
      setDone(true);
      setTimeout(() => nav('/login'), 1500);
    } catch (err) {
      const d = err.detail;
      setError(
        typeof d === 'string' ? d :
          Array.isArray(d) ? d.map(e => e.msg || e).join(' ، ') :
            err.error || t('registerError')
      );
    } finally { setLoading(false); }
  };

  const PATIENT_FIELDS = [
    { key: 'full_name', label: t('fullName'), ph: lang === 'ar' ? 'سارة عبدالله' : 'Sarah Abdullah', type: 'text' },
    { key: 'clinic_email', label: lang === 'ar' ? 'البريد الإلكتروني للعيادة (المطلوب الانضمام إليها)' : 'Clinic Email', ph: 'clinic@mail.com', type: 'email', dir: 'ltr' },
    { key: 'email', label: t('email'), ph: 'example@mail.com', type: 'email', dir: 'ltr' },
    { key: 'phone_number', label: t('phoneNumber'), ph: '01012345678', type: 'text', dir: 'ltr' },
    { key: 'password', label: t('password'), ph: t('minChars'), type: 'password' },
  ];

  const DOCTOR_FIELDS = [
    { key: 'full_name', label: lang === 'ar' ? 'اسم الطبيب / الدكتور' : 'Doctor Name', ph: lang === 'ar' ? 'د. أحمد محمود' : 'Dr. Ahmed Mahmoud', type: 'text' },
    { key: 'specialization', label: lang === 'ar' ? 'التخصص الطبي' : 'Medical Specialization', ph: lang === 'ar' ? 'قلب وأوعية دموية' : 'Cardiology', type: 'text' },
    { key: 'clinic_email', label: lang === 'ar' ? 'البريد الإلكتروني للعيادة (التي تعمل بها) *' : 'Clinic Email *', ph: 'clinic@mail.com', type: 'email', dir: 'ltr' },
    { key: 'email', label: lang === 'ar' ? 'البريد الإلكتروني الخاص بالطبيب (للدخول)' : 'Doctor Email (for Login)', ph: 'doctor@mail.com', type: 'email', dir: 'ltr' },
    { key: 'phone_number', label: lang === 'ar' ? 'رقم الهاتف والتواصل' : 'Contact Number', ph: '01012345678', type: 'text', dir: 'ltr' },
    { key: 'password', label: t('password'), ph: t('minChars'), type: 'password' },
  ];

  const LAB_FIELDS = [
    { key: 'full_name', label: lang === 'ar' ? 'اسم معمل التحاليل' : 'Laboratory Name', ph: lang === 'ar' ? 'معمل البرج للتحاليل' : 'Al-Borg Lab', type: 'text' },
    { key: 'clinic_email', label: lang === 'ar' ? 'البريد الإلكتروني للعيادة (المرتبطة) *' : 'Clinic Email *', ph: 'clinic@mail.com', type: 'email', dir: 'ltr' },
    { key: 'email', label: lang === 'ar' ? 'البريد الإلكتروني للمعمل (للدخول)' : 'Lab Email (for Login)', ph: 'lab@mail.com', type: 'email', dir: 'ltr' },
    { key: 'phone_number', label: lang === 'ar' ? 'رقم الهاتف' : 'Phone Number', ph: '01012345678', type: 'text', dir: 'ltr' },
    { key: 'password', label: t('password'), ph: t('minChars'), type: 'password' },
  ];

  const CLINIC_OWNER_FIELDS = [
    { key: 'full_name', label: lang === 'ar' ? 'اسم العيادة *' : 'Clinic Name *', ph: lang === 'ar' ? 'عيادة النور التخصصية' : 'Al-Noor Clinic', type: 'text' },
    { key: 'email', label: lang === 'ar' ? 'البريد الإلكتروني للعيادة (الرئيسي) *' : 'Clinic Main Email *', ph: 'owner@mail.com', type: 'email', dir: 'ltr' },
    { key: 'phone_number', label: lang === 'ar' ? 'رقم الهاتف والتواصل' : 'Contact Number', ph: '01012345678', type: 'text', dir: 'ltr' },
    { key: 'address', label: lang === 'ar' ? 'عنوان العيادة' : 'Clinic Address', ph: lang === 'ar' ? 'القاهرة، المعادي...' : 'Cairo, Maadi...', type: 'text' },
    { key: 'specialization', label: lang === 'ar' ? 'التخصصات (مفصولة بفاصلة)' : 'Specializations (comma separated)', ph: lang === 'ar' ? 'قلب، عظام، باطنة' : 'cardiology, orthopedics', type: 'text' },
    { key: 'location_url', label: lang === 'ar' ? 'رابط موقع العيادة على خرائط جوجل (Google Maps URL)' : 'Google Maps Location URL', ph: 'https://maps.google.com/?q=...', type: 'url', dir: 'ltr' },
    { key: 'password', label: t('password'), ph: t('minChars'), type: 'password' },
  ];

  const fields = role === 'doctor' ? DOCTOR_FIELDS : role === 'lab' ? LAB_FIELDS : role === 'clinic_owner' ? CLINIC_OWNER_FIELDS : PATIENT_FIELDS;

  return (
    <div className="auth-page">
      <div className="auth-side">
        <div className="auth-dots" />
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 400 }}>
          <img src="/clinicon-logo.png" alt="Clinicon"
            style={{ height: 64, marginBottom: 24, filter: 'brightness(0) invert(1) brightness(0.95)' }} />
          <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12, color: '#EAF2F0' }}>
            Clinicon
          </h1>
          <p style={{ fontSize: 15, color: 'rgba(234,242,240,0.7)', lineHeight: 1.9 }}>
            {role === 'doctor' ? t('adminBrandDesc') : role === 'lab' ? 'منصة إدارة نتائج التحاليل والتواصل الفعال مع المرضى' : role === 'clinic_owner' ? 'إدارة شاملة لدكاترة ومعامل ومعلومات العيادات' : t('patientBrandDesc')}
          </p>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-form">
          {done ? (
            <div style={{ textAlign: 'center', padding: '48px 0' }}>
              <div style={{
                width: 62, height: 62, borderRadius: '50%',
                background: 'var(--primary-light)', display: 'grid', placeItems: 'center',
                margin: '0 auto 20px', color: 'var(--primary)', fontSize: 26, fontWeight: 700,
              }}>✓</div>
              <h2 style={{ fontSize: 23, fontWeight: 700, marginBottom: 8 }}>{t('accountCreated')}</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{t('redirecting')}</p>
            </div>
          ) : !role ? (
            /* Role Picker */
            <>
              <div style={{ marginBottom: 28 }}>
                <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
                  {t('createAccount')}
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 13.5 }}>
                  {t('accountTypeQ')}
                </p>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                <button onClick={() => setRole('patient')} className="role-option">
                  <div className="role-option-icon" style={{ background: 'var(--primary-light)', color: 'var(--primary)' }}>
                    <User size={24} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>{t('patientRole')}</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.5 }}>{t('patientRoleDesc')}</div>
                  </div>
                </button>

                <button onClick={() => setRole('doctor')} className="role-option">
                  <div className="role-option-icon" style={{ background: '#FFF3E0', color: '#E65100' }}>
                    <Building2 size={24} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>طبيب / دكتور (Doctor)</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.5 }}>حساب طبيب للكشف ومتابعة الطابور والروشتات وإضافة الموقع على خرائط جوجل</div>
                  </div>
                </button>

                <button onClick={() => setRole('clinic_owner')} className="role-option">
                  <div className="role-option-icon" style={{ background: '#E8F5E9', color: '#2E7D32' }}>
                    <Building2 size={24} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>مالك عيادة (Clinic Owner)</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.5 }}>حساب إداري لإدارة العيادة وإضافة الدكاترة والمعامل والمعلومات الأساسية</div>
                  </div>
                </button>

                <button onClick={() => setRole('lab')} className="role-option">
                  <div className="role-option-icon" style={{ background: '#E3F2FD', color: '#1565C0' }}>
                    <FlaskConical size={24} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>معمل تحاليل (Lab)</div>
                    <div style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.5 }}>حساب لمعامل التحاليل لرفع نتائج التحاليل للمرضى وإرسال إشعارات تلقائية</div>
                  </div>
                </button>
              </div>

              <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-muted)', marginTop: 24 }}>
                {t('haveAccount')}{' '}
                <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 700, textDecoration: 'none' }}>
                  {t('loginHere')}
                </Link>
              </p>
            </>
          ) : (
            /* Registration Form */
            <>
              <div style={{ marginBottom: 28 }}>
                <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
                  {role === 'doctor' ? t('clinicRegister') : t('createAccount')}
                </h2>
                <p style={{ color: 'var(--text-muted)', fontSize: 13.5 }}>
                  {role === 'doctor' ? t('clinicRegisterSub') : t('registerSub')}
                </p>
              </div>

              <button onClick={() => { setRole(null); setError(''); }}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--primary)', fontSize: 13, fontWeight: 600,
                  marginBottom: 16, padding: 0, display: 'flex', alignItems: 'center', gap: 4,
                }}>
                ← {t('changeRole')}
              </button>

              {error && <div className="error-box" style={{ marginBottom: 20 }}>{error}</div>}

              <form onSubmit={handleSubmit}>
                {fields.map(({ key, label, ph, type, dir }) => (
                  <div key={key} style={{ marginBottom: 18 }}>
                    <label className="label">{label}</label>
                    <input type={type} value={form[key]} onChange={set(key)}
                      required={key !== 'phone_number' && key !== 'specialization'} placeholder={ph}
                      className="input-field"
                      style={dir ? { direction: dir, textAlign: lang === 'ar' ? 'right' : 'left' } : {}}
                      minLength={key === 'password' ? 8 : undefined} />
                  </div>
                ))}

                {role === 'doctor' && (
                  <div style={{
                    marginBottom: 20,
                    padding: '16px 18px',
                    borderRadius: 14,
                    background: 'var(--bg-card, #F8FAFC)',
                    border: '1px solid var(--border, #E2E8F0)'
                  }}>
                    <label className="label" style={{ fontWeight: 700, marginBottom: 12, display: 'block' }}>
                      {lang === 'ar' ? 'أيام وساعات العمل لكل يوم *' : 'Working Days & Hours per Day *'}
                    </label>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                      {DAYS.map(day => {
                        const sched = daySchedules[day.id] || { active: false, start_time: '09:00', end_time: '17:00' };
                        return (
                          <div key={day.id} style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            gap: 8,
                            padding: '8px 12px',
                            borderRadius: 10,
                            background: sched.active ? '#ffffff' : 'transparent',
                            border: sched.active ? '1px solid var(--border, #CBD5E1)' : '1px dashed #CBD5E1',
                            transition: 'all 0.15s ease'
                          }}>
                            {/* Toggle Button */}
                            <button
                              type="button"
                              onClick={() => toggleDayActive(day.id)}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 6,
                                padding: '5px 12px',
                                borderRadius: 20,
                                border: sched.active ? '1.5px solid var(--primary)' : '1px solid #CBD5E1',
                                background: sched.active ? 'var(--primary-light, #E3F2FD)' : '#F1F5F9',
                                color: sched.active ? 'var(--primary, #1565C0)' : '#64748B',
                                fontWeight: sched.active ? 700 : 500,
                                fontSize: 13,
                                cursor: 'pointer',
                                minWidth: 90
                              }}
                            >
                              {sched.active ? '✓ ' : ''}{lang === 'ar' ? day.labelAr : day.labelEn}
                            </button>

                            {/* Hours Inputs per Day */}
                            {sched.active ? (
                              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{lang === 'ar' ? 'من' : 'From'}</span>
                                <input
                                  type="time"
                                  value={sched.start_time}
                                  onChange={e => updateDayTime(day.id, 'start_time', e.target.value)}
                                  className="input-field"
                                  style={{ padding: '4px 8px', fontSize: 13, width: 105 }}
                                  required={sched.active}
                                />
                                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{lang === 'ar' ? 'إلى' : 'To'}</span>
                                <input
                                  type="time"
                                  value={sched.end_time}
                                  onChange={e => updateDayTime(day.id, 'end_time', e.target.value)}
                                  className="input-field"
                                  style={{ padding: '4px 8px', fontSize: 13, width: 105 }}
                                  required={sched.active}
                                />
                              </div>
                            ) : (
                              <span style={{ fontSize: 12, color: '#94A3B8', fontStyle: 'italic' }}>
                                {lang === 'ar' ? 'إجازة / غير متاح' : 'Off Duty'}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                <button type="submit" disabled={loading} className="btn-primary"
                  style={{ width: '100%', padding: 14, fontSize: 15, marginTop: 8 }}>
                  {loading ? t('registering') : t('register')}
                </button>
              </form>

              <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-muted)', marginTop: 24 }}>
                {t('haveAccount')}{' '}
                <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 700, textDecoration: 'none' }}>
                  {t('loginHere')}
                </Link>
              </p>

              <div style={{
                display: 'flex', alignItems: 'center', gap: 6,
                justifyContent: 'center', marginTop: 32,
                color: 'var(--text-muted)', fontSize: 12,
              }}>
                <Shield size={14} /> {t('secureData')}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
