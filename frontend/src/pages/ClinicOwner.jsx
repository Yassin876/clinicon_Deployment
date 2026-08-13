import { useState, useEffect } from 'react';
import { Plus, Building2, FlaskConical, User, Key, CheckCircle2, ChevronRight, Loader2, Clock, Check, X, Pencil } from 'lucide-react';
import { getMyClinic, registerClinic, updateClinic, getMyClinicDoctors, addClinicMember, getMyLabs, getPendingClinicRequests, approveClinicRequest, rejectClinicRequest } from '../utils/api';
import { useLang } from '../context/LangContext';
import { useToast } from '../context/ToastContext';

export default function ClinicOwner() {
  const { lang } = useLang();
  const toast = useToast();
  const [tab, setTab] = useState('pending');

  // Clinic setup
  const [clinic, setClinic] = useState(null);
  const [clinicLoading, setClinicLoading] = useState(true);
  const [showClinicForm, setShowClinicForm] = useState(false);
  const [showEditClinic, setShowEditClinic] = useState(false);
  const [clinicForm, setClinicForm] = useState({ clinic_name: '', address: '', phone: '', location_url: '', specializations: '' });
  const [clinicSaving, setClinicSaving] = useState(false);

  // Doctors
  const [doctors, setDoctors] = useState([]);
  const [showAddMember, setShowAddMember] = useState(false);
  const [memberForm, setMemberForm] = useState({
    role: 'doctor',
    full_name: '',
    email: '',
    password: '',
    phone_number: '',
    specialization: '',
    bio: '',
    location_url: '',
    availabilities: []
  });
  const [memberSaving, setMemberSaving] = useState(false);

  // Labs
  const [labs, setLabs] = useState([]);
  const [showAddLab, setShowAddLab] = useState(false);
  const [labForm, setLabForm] = useState({ name: '', contact_info: '' });
  const [labSaving, setLabSaving] = useState(false);

  // Pending Requests
  const [pendingRequests, setPendingRequests] = useState([]);
  const [pendingLoading, setPendingLoading] = useState(false);
  const [actionUserId, setActionUserId] = useState(null);

  // Load clinic on mount
  useEffect(() => {
    getMyClinic()
      .then(data => {
        setClinic(data);
        if (data) {
          setClinicForm({
            clinic_name: data.clinic_name || '',
            address: data.address || '',
            phone: data.phone || '',
            location_url: data.location_url || '',
            specializations: data.specializations || ''
          });
        }
        setClinicLoading(false);
      })
      .catch(() => { setClinic(null); setClinicLoading(false); });
  }, []);

  const loadPendingRequests = () => {
    setPendingLoading(true);
    getPendingClinicRequests()
      .then(r => setPendingRequests(r.requests || []))
      .catch(() => setPendingRequests([]))
      .finally(() => setPendingLoading(false));
  };

  // Load tab data
  useEffect(() => {
    if (!clinic) return;
    if (tab === 'pending') {
      loadPendingRequests();
    } else if (tab === 'doctors') {
      getMyClinicDoctors().then(r => setDoctors(r.doctors || [])).catch(() => setDoctors([]));
    } else if (tab === 'labs') {
      getMyLabs().then(r => setLabs(r.labs || [])).catch(() => setLabs([]));
    }
  }, [tab, clinic]);

  const handleApprove = async (userId) => {
    setActionUserId(userId);
    try {
      const res = await approveClinicRequest(userId);
      toast(res.message || (lang === 'ar' ? 'تمت الموافقة بنجاح' : 'Approved successfully'), 'success');
      loadPendingRequests();
    } catch (err) {
      toast(err.detail || (lang === 'ar' ? 'حدث خطأ' : 'Error'), 'error');
    } finally { setActionUserId(null); }
  };

  const handleReject = async (userId) => {
    if (!window.confirm(lang === 'ar' ? 'هل أنت تأكد من رفض هذا الطلب؟' : 'Are you sure you want to reject this request?')) return;
    setActionUserId(userId);
    try {
      const res = await rejectClinicRequest(userId);
      toast(res.message || (lang === 'ar' ? 'تم الرفض' : 'Rejected'), 'info');
      loadPendingRequests();
    } catch (err) {
      toast(err.detail || (lang === 'ar' ? 'حدث خطأ' : 'Error'), 'error');
    } finally { setActionUserId(null); }
  };

  const handleRegisterClinic = async (e) => {
    e.preventDefault();
    if (!clinicForm.clinic_name.trim()) return;
    setClinicSaving(true);
    try {
      const res = await registerClinic(clinicForm);
      setClinic(res.clinic);
      setShowClinicForm(false);
      toast(lang === 'ar' ? 'تم تسجيل العيادة بنجاح!' : 'Clinic registered successfully!', 'success');
    } catch (err) {
      toast(err.detail || (lang === 'ar' ? 'حدث خطأ' : 'Error occurred'), 'error');
    } finally { setClinicSaving(false); }
  };

  const handleUpdateClinic = async (e) => {
    e.preventDefault();
    setClinicSaving(true);
    try {
      const res = await updateClinic(clinicForm);
      setClinic(res.clinic);
      setShowEditClinic(false);
      toast(lang === 'ar' ? 'تم تحديث بيانات العيادة بنجاح!' : 'Clinic updated successfully!', 'success');
    } catch (err) {
      toast(err.detail || (lang === 'ar' ? 'حدث خطأ' : 'Error occurred'), 'error');
    } finally { setClinicSaving(false); }
  };

  const handleAddMember = async (e) => {
    e.preventDefault();
    if (!memberForm.full_name.trim() || !memberForm.email.trim() || !memberForm.password.trim()) return;
    if (memberForm.role === 'doctor' && !memberForm.specialization.trim()) return;
    setMemberSaving(true);
    try {
      const payload = {
        ...memberForm,
        role: memberForm.role,
        availabilities: memberForm.role === 'doctor' ? memberForm.availabilities : undefined,
      };
      await addClinicMember(payload);
      setMemberForm({
        role: 'doctor',
        full_name: '',
        email: '',
        password: '',
        phone_number: '',
        specialization: '',
        bio: '',
        location_url: '',
        availabilities: []
      });
      setShowAddMember(false);
      getMyClinicDoctors().then(r => setDoctors(r.doctors || [])).catch(() => { });
      toast(lang === 'ar' ? 'تم إضافة العضو بنجاح!' : 'Member added successfully!', 'success');
    } catch (err) {
      toast(err.detail || (lang === 'ar' ? 'حدث خطأ' : 'Error occurred'), 'error');
    } finally { setMemberSaving(false); }
  };

  const handleAddLab = async (e) => {
    e.preventDefault();
    if (!labForm.name.trim()) return;
    setLabSaving(true);
    try {
      await addLab(labForm);
      setLabForm({ name: '', contact_info: '' });
      setShowAddLab(false);
      const r = await getMyLabs();
      setLabs(r.labs || []);
      toast(lang === 'ar' ? 'تم إضافة المعمل بنجاح!' : 'Lab added successfully!', 'success');
    } catch (err) {
      toast(err.detail || (lang === 'ar' ? 'حدث خطأ' : 'Error occurred'), 'error');
    } finally { setLabSaving(false); }
  };

  const ar = lang === 'ar';

  // ── If no clinic yet ──
  if (clinicLoading) return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
      <Loader2 size={28} style={{ animation: 'spin 1s linear infinite' }} />
    </div>
  );

  if (!clinic && !showClinicForm) return (
    <div className="fade-up" style={{ maxWidth: 560, margin: '0 auto' }}>
      <div className="card" style={{
        background: 'linear-gradient(135deg, #1E88E5 0%, #1565C0 100%)',
        color: '#fff', padding: '36px 32px', borderRadius: 20, textAlign: 'center', marginBottom: 28
      }}>
        <Building2 size={52} style={{ marginBottom: 16, opacity: 0.9 }} />
        <h2 style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>
          {ar ? 'مرحباً بك في نظام إدارة العيادة' : 'Welcome to Clinic Management'}
        </h2>
        <p style={{ marginTop: 10, opacity: 0.85, fontSize: 15 }}>
          {ar ? 'لم تقم بتسجيل عيادتك بعد. ابدأ الآن لإدارة دكاترتك ومعاملك وموقع العيادة.' : 'You haven\'t registered your clinic yet. Get started to manage your doctors and labs.'}
        </p>
        <button
          onClick={() => setShowClinicForm(true)}
          className="btn-primary"
          style={{ marginTop: 24, padding: '12px 28px', background: 'rgba(255,255,255,0.2)', border: '2px solid rgba(255,255,255,0.5)', fontSize: 15, color: '#fff' }}
        >
          <Plus size={18} /> {ar ? 'تسجيل عيادة الآن' : 'Register Clinic Now'}
        </button>
      </div>
    </div>
  );

  if (showClinicForm || showEditClinic) return (
    <div className="fade-up" style={{ maxWidth: 520, margin: '0 auto' }}>
      <div className="card" style={{ padding: 32, borderRadius: 20 }}>
        <h2 style={{ fontSize: 20, fontWeight: 800, marginBottom: 24 }}>
          <Building2 size={22} style={{ marginInlineEnd: 10, color: 'var(--primary)' }} />
          {showEditClinic ? (ar ? 'تعديل بيانات العيادة' : 'Edit Clinic Info') : (ar ? 'تسجيل عيادة جديدة' : 'Register New Clinic')}
        </h2>
        <form onSubmit={showEditClinic ? handleUpdateClinic : handleRegisterClinic} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label className="label">{ar ? 'اسم العيادة *' : 'Clinic Name *'}</label>
            <input className="input-field" value={clinicForm.clinic_name} required
              onChange={e => setClinicForm({ ...clinicForm, clinic_name: e.target.value })}
              placeholder={ar ? 'عيادة النور التخصصية...' : 'Al-Noor Clinic...'} />
          </div>
          <div>
            <label className="label">{ar ? 'العنوان' : 'Address'}</label>
            <input className="input-field" value={clinicForm.address}
              onChange={e => setClinicForm({ ...clinicForm, address: e.target.value })}
              placeholder={ar ? 'شارع التحرير، المعادي...' : 'Street, City...'} />
          </div>
          <div>
            <label className="label">{ar ? 'رابط موقع العيادة على خرائط جوجل (Google Maps URL)' : 'Google Maps Location URL'}</label>
            <input className="input-field" value={clinicForm.location_url} type="url" dir="ltr"
              onChange={e => setClinicForm({ ...clinicForm, location_url: e.target.value })}
              placeholder="https://maps.google.com/?q=..." />
          </div>
          <div>
            <label className="label">{ar ? 'رقم الهاتف' : 'Phone'}</label>
            <input className="input-field" value={clinicForm.phone}
              onChange={e => setClinicForm({ ...clinicForm, phone: e.target.value })} />
          </div>
          <div>
            <label className="label">{ar ? 'التخصصات (مفصولة بفاصلة)' : 'Specializations (comma-separated)'}</label>
            <input className="input-field" value={clinicForm.specializations}
              onChange={e => setClinicForm({ ...clinicForm, specializations: e.target.value })}
              placeholder={ar ? 'قلب، عظام، باطنة' : 'cardiology, orthopedics, internal medicine'} />
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button type="submit" className="btn-primary" disabled={clinicSaving} style={{ flex: 1, padding: 13 }}>
              {clinicSaving ? (ar ? 'جاري الحفظ...' : 'Saving...') : (ar ? 'حفظ البيانات' : 'Save Info')}
            </button>
            <button type="button" className="btn-secondary" style={{ padding: 13 }} onClick={() => { setShowClinicForm(false); setShowEditClinic(false); }}>
              {ar ? 'إلغاء' : 'Cancel'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  // ── Main Dashboard ──
  return (
    <div className="fade-up">
      {/* Clinic Banner */}
      <div className="card" style={{
        background: 'linear-gradient(135deg, #1565C0 0%, #0D47A1 100%)',
        color: '#fff', padding: '20px 28px', borderRadius: 16, marginBottom: 24,
        display: 'flex', alignItems: 'center', gap: 16
      }}>
        <div style={{
          width: 50, height: 50, borderRadius: 12,
          background: 'rgba(255,255,255,0.15)', display: 'grid', placeItems: 'center'
        }}>
          <Building2 size={26} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 20, fontWeight: 800 }}>{clinic.clinic_name}</div>
          {clinic.address && <div style={{ opacity: 0.8, fontSize: 13, marginTop: 2 }}>📍 {clinic.address}</div>}
          {clinic.location_url && (
            <div style={{ marginTop: 4 }}>
              <a href={clinic.location_url} target="_blank" rel="noopener noreferrer"
                style={{ color: '#90CAF9', fontSize: 12.5, textDecoration: 'underline', fontWeight: 600 }}>
                🗺️ {ar ? 'رابط خرائط جوجل' : 'Google Maps Location'}
              </a>
            </div>
          )}
          {clinic.specializations && (
            <div style={{ marginTop: 6, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {clinic.specializations.split(',').map((s, i) => (
                <span key={i} style={{
                  background: 'rgba(255,255,255,0.2)', padding: '2px 10px',
                  borderRadius: 20, fontSize: 11.5, fontWeight: 600
                }}>{s.trim()}</span>
              ))}
            </div>
          )}
        </div>
        <button
          onClick={() => {
            setClinicForm({
              clinic_name: clinic.clinic_name || '',
              address: clinic.address || '',
              phone: clinic.phone || '',
              location_url: clinic.location_url || '',
              specializations: clinic.specializations || ''
            });
            setShowEditClinic(true);
          }}
          className="btn-secondary"
          style={{
            background: 'rgba(255,255,255,0.2)', borderColor: 'rgba(255,255,255,0.4)',
            color: '#fff', padding: '8px 14px', fontSize: 12.5
          }}
        >
          <Pencil size={14} /> {ar ? 'تعديل البيانات' : 'Edit Info'}
        </button>
      </div>

      {/* Tabs */}
      <div className="rec-tabs" style={{ marginBottom: 20 }}>
        {[
          { id: 'pending', icon: Clock, label: ar ? `طلبات الانضمام (${pendingRequests.length})` : `Pending (${pendingRequests.length})` },
          { id: 'doctors', icon: User, label: ar ? 'الدكاترة' : 'Doctors' },
          { id: 'labs', icon: FlaskConical, label: ar ? 'المعامل' : 'Labs' },
        ].map(({ id, icon: Icon, label }) => (
          <button key={id} onClick={() => setTab(id)} className={`rec-tab ${tab === id ? 'active' : ''}`}>
            <Icon size={14} style={{ opacity: 0.7 }} /> {label}
          </button>
        ))}
      </div>

      {/* ─── Pending Requests Tab ─── */}
      {tab === 'pending' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ fontSize: 13.5, color: 'var(--text-muted)' }}>
              {pendingRequests.length} {ar ? 'طلب انضمام معلق' : 'pending request(s)'}
            </div>
            <button className="btn-secondary" style={{ padding: '7px 14px', fontSize: 12.5 }} onClick={loadPendingRequests}>
              🔄 {ar ? 'تحديث' : 'Refresh'}
            </button>
          </div>

          {pendingLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
              <Loader2 size={24} style={{ animation: 'spin 1s linear infinite' }} />
            </div>
          ) : pendingRequests.length === 0 ? (
            <div className="sphg-card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
              <Clock size={36} style={{ marginBottom: 10, opacity: 0.5 }} />
              <div style={{ fontWeight: 600, fontSize: 15 }}>
                {ar ? 'لا توجد طلبات انضمام معلقة حالياً' : 'No pending join requests'}
              </div>
              <div style={{ fontSize: 13, marginTop: 4, opacity: 0.7 }}>
                {ar ? 'عندما يدخل طبيب أو معمل أو مريض بريد عيادتك أثناء التسجيل، ستظهر طلباتهم هنا للموافقة عليها.' : 'Requests will appear here when doctors, labs, or patients register using your clinic email.'}
              </div>
            </div>
          ) : (
            <div className="sphg-card">
              {pendingRequests.map((req, i) => {
                const roleBadge = req.role === 'doctor' ? (ar ? 'طبيب' : 'Doctor') : req.role === 'lab' ? (ar ? 'معمل' : 'Lab') : (ar ? 'مريض' : 'Patient');
                const roleColor = req.role === 'doctor' ? '#1E88E5' : req.role === 'lab' ? '#8E24AA' : '#43A047';
                return (
                  <div key={req.id || i} style={{
                    padding: '16px 20px', borderBottom: i < pendingRequests.length - 1 ? '1px solid var(--border-light)' : 'none',
                    display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap'
                  }}>
                    <div style={{
                      width: 44, height: 44, borderRadius: 12,
                      background: `${roleColor}15`, display: 'grid', placeItems: 'center'
                    }}>
                      <User size={20} color={roleColor} />
                    </div>
                    <div style={{ flex: 1, minWidth: 200 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontWeight: 700, fontSize: 15 }}>{req.full_name}</span>
                        <span style={{
                          fontSize: 11, padding: '2px 8px', borderRadius: 12, fontWeight: 700,
                          background: `${roleColor}20`, color: roleColor
                        }}>{roleBadge}</span>
                      </div>
                      <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 3 }}>
                        ✉️ {req.email} {req.phone_number ? ` | 📞 ${req.phone_number}` : ''}
                      </div>
                      {req.specialization && (
                        <div style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 600, marginTop: 2 }}>
                          🩺 {req.specialization}
                        </div>
                      )}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        onClick={() => handleApprove(req.id)}
                        disabled={actionUserId === req.id}
                        className="btn-primary"
                        style={{ padding: '8px 16px', fontSize: 13, background: '#2E7D32', borderColor: '#2E7D32' }}
                      >
                        <Check size={15} /> {ar ? 'موافقة وتفعيل' : 'Approve'}
                      </button>
                      <button
                        onClick={() => handleReject(req.id)}
                        disabled={actionUserId === req.id}
                        className="btn-secondary"
                        style={{ padding: '8px 14px', fontSize: 13, color: '#C62828', borderColor: '#FFCDD2' }}
                      >
                        <X size={15} /> {ar ? 'رفض' : 'Reject'}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* ─── Doctors Tab ─── */}
      {tab === 'doctors' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ fontSize: 13.5, color: 'var(--text-muted)' }}>
              {doctors.length} {ar ? 'دكتور مرتبط' : 'linked doctor(s)'}
            </div>
            <button className="btn-primary" style={{ padding: '9px 16px', fontSize: 13.5 }}
              onClick={() => setShowAddMember(!showAddMember)}>
              <Plus size={15} /> {ar ? 'إضافة عضو' : 'Add Member'}
            </button>
          </div>

          {/* Add Member Form */}
          {showAddMember && (
            <div className="card" style={{ padding: 22, marginBottom: 16, borderRadius: 14 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 14 }}>
                {ar ? 'إضافة عضو جديد إلى العيادة' : 'Add a new member to the clinic'}
              </div>
              <form onSubmit={handleAddMember} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', gap: 10 }}>
                  <label style={{ flex: 1 }}>
                    <span className="label">{ar ? 'النوع' : 'Role'}</span>
                    <select className="input-field" value={memberForm.role} onChange={e => setMemberForm({ ...memberForm, role: e.target.value })}>
                      <option value="doctor">{ar ? 'طبيب' : 'Doctor'}</option>
                      <option value="lab">{ar ? 'معمل' : 'Lab'}</option>
                    </select>
                  </label>
                </div>
                <input className="input-field" value={memberForm.full_name} required
                  onChange={e => setMemberForm({ ...memberForm, full_name: e.target.value })}
                  placeholder={ar ? 'الاسم الكامل *' : 'Full name *'} />
                <input className="input-field" value={memberForm.email} required type="email"
                  onChange={e => setMemberForm({ ...memberForm, email: e.target.value })}
                  placeholder={ar ? 'البريد الإلكتروني *' : 'Email *'} />
                <input className="input-field" value={memberForm.password} required type="password"
                  onChange={e => setMemberForm({ ...memberForm, password: e.target.value })}
                  placeholder={ar ? 'كلمة المرور *' : 'Password *'} />
                <input className="input-field" value={memberForm.phone_number}
                  onChange={e => setMemberForm({ ...memberForm, phone_number: e.target.value })}
                  placeholder={ar ? 'رقم الهاتف' : 'Phone number'} />
                {memberForm.role === 'doctor' && (
                  <>
                    <input className="input-field" value={memberForm.specialization} required
                      onChange={e => setMemberForm({ ...memberForm, specialization: e.target.value })}
                      placeholder={ar ? 'التخصص *' : 'Specialization *'} />
                    <input className="input-field" value={memberForm.bio}
                      onChange={e => setMemberForm({ ...memberForm, bio: e.target.value })}
                      placeholder={ar ? 'نبذة مختصرة (اختياري)' : 'Bio (optional)'} />
                    <input className="input-field" value={memberForm.location_url} type="url"
                      onChange={e => setMemberForm({ ...memberForm, location_url: e.target.value })}
                      placeholder={ar ? 'رابط الموقع (اختياري)' : 'Location URL (optional)'} />
                  </>
                )}
                <div style={{ display: 'flex', gap: 10 }}>
                  <button type="submit" className="btn-primary" disabled={memberSaving} style={{ flex: 1, padding: 11 }}>
                    {memberSaving ? (ar ? 'جاري الإضافة...' : 'Adding...') : (ar ? 'إضافة العضو' : 'Add Member')}
                  </button>
                  <button type="button" className="btn-secondary" style={{ padding: 11 }} onClick={() => setShowAddMember(false)}>
                    {ar ? 'إلغاء' : 'Cancel'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Doctors List */}
          <div className="sphg-card">
            {doctors.length === 0 ? (
              <div style={{ padding: 36, textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
                {ar ? 'لا يوجد دكاترة مرتبطون بعد. استخدم زر "إضافة عضو" لإضافة دكتور.' : 'No doctors linked yet. Use "Add Member" to add one.'}
              </div>
            ) : doctors.map((doc, i) => (
              <div key={doc.id || i} style={{
                padding: '14px 22px', borderBottom: i < doctors.length - 1 ? '1px solid var(--border-light)' : 'none',
                display: 'flex', alignItems: 'center', gap: 14
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: 'var(--primary-light)', display: 'grid', placeItems: 'center'
                }}>
                  <User size={18} color="var(--primary)" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 14.5 }}>{doc.name}</div>
                  <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 2 }}>{doc.specialization}</div>
                  
                  {/* Doctor Working Days & Hours */}
                  {doc.weekly_schedule && doc.weekly_schedule.length > 0 ? (
                    <div style={{ marginTop: 8, display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                      <span style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--primary)' }}>📅 المواعيد والأيام:</span>
                      {doc.weekly_schedule.map((sch, sIdx) => {
                        const dayNames = {
                          '0': 'الإثنين', '1': 'الثلاثاء', '2': 'الأربعاء', '3': 'الخميس',
                          '4': 'الجمعة', '5': 'السبت', '6': 'الأحد',
                          'monday': 'الإثنين', 'tuesday': 'الثلاثاء', 'wednesday': 'الأربعاء',
                          'thursday': 'الخميس', 'friday': 'الجمعة', 'saturday': 'السبت', 'sunday': 'الأحد'
                        };
                        const dayLabel = dayNames[String(sch.day_of_week).toLowerCase()] || sch.day_of_week;
                        return (
                          <span key={sIdx} style={{
                            fontSize: 11, background: 'var(--primary-tint, #e0f2fe)', color: 'var(--primary, #0284c7)',
                            padding: '3px 8px', borderRadius: 6, fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4
                          }}>
                            {dayLabel}: {sch.start_time} - {sch.end_time}
                          </span>
                        );
                      })}
                    </div>
                  ) : (
                    <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 6 }}>
                      🕒 لم يتم تحديد جدول أسبوعي بعد
                    </div>
                  )}
                </div>
                <span style={{
                  fontSize: 11.5, padding: '3px 10px', borderRadius: 20, fontWeight: 600,
                  background: doc.is_active ? '#E8F5E9' : '#FFEBEE',
                  color: doc.is_active ? '#2E7D32' : '#C62828'
                }}>
                  {doc.is_active ? (ar ? 'نشط' : 'Active') : (ar ? 'غير نشط' : 'Inactive')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Labs Tab ─── */}
      {tab === 'labs' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ fontSize: 13.5, color: 'var(--text-muted)' }}>
              {labs.length} {ar ? 'معمل مرتبط' : 'linked lab(s)'}
            </div>
            <button className="btn-primary" style={{ padding: '9px 16px', fontSize: 13.5 }}
              onClick={() => setShowAddLab(!showAddLab)}>
              <Plus size={15} /> {ar ? 'إضافة معمل' : 'Add Lab'}
            </button>
          </div>

          {/* Add Lab Form */}
          {showAddLab && (
            <div className="card" style={{ padding: 22, marginBottom: 16, borderRadius: 14 }}>
              <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 14 }}>
                {ar ? 'بيانات المعمل الجديد' : 'New Lab Details'}
              </div>
              <form onSubmit={handleAddLab} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <input className="input-field" value={labForm.name} required
                  onChange={e => setLabForm({ ...labForm, name: e.target.value })}
                  placeholder={ar ? 'اسم المعمل *' : 'Lab name *'} />
                <input className="input-field" value={labForm.contact_info}
                  onChange={e => setLabForm({ ...labForm, contact_info: e.target.value })}
                  placeholder={ar ? 'بيانات التواصل (هاتف، عنوان...)' : 'Contact info (phone, address...)'} />
                <div style={{ display: 'flex', gap: 10 }}>
                  <button type="submit" className="btn-primary" disabled={labSaving} style={{ flex: 1, padding: 11 }}>
                    {labSaving ? (ar ? 'جاري الحفظ...' : 'Saving...') : (ar ? 'إضافة المعمل' : 'Add Lab')}
                  </button>
                  <button type="button" className="btn-secondary" style={{ padding: 11 }} onClick={() => setShowAddLab(false)}>
                    {ar ? 'إلغاء' : 'Cancel'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Labs List */}
          <div className="sphg-card">
            {labs.length === 0 ? (
              <div style={{ padding: 36, textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
                {ar ? 'لا توجد معامل مرتبطة بعد. اضغط "إضافة معمل" لإضافة واحد.' : 'No labs linked yet. Click "Add Lab" to add one.'}
              </div>
            ) : labs.map((lab, i) => (
              <div key={lab.id || i} style={{
                padding: '14px 22px', borderBottom: i < labs.length - 1 ? '1px solid var(--border-light)' : 'none',
                display: 'flex', alignItems: 'center', gap: 14
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  background: '#E3F2FD', display: 'grid', placeItems: 'center'
                }}>
                  <FlaskConical size={18} color="#1565C0" />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 14.5 }}>{lab.name}</div>
                  {lab.contact_info && <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 2 }}>📞 {lab.contact_info}</div>}
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--text-faint)' }}>
                  {lab.added_at ? new Date(lab.added_at).toLocaleDateString(lang === 'ar' ? 'ar-EG' : 'en-US') : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
