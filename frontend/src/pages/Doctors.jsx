import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, ArrowRight, User, MapPin } from 'lucide-react';
import { getDoctors } from '../utils/api';
import { getClinicMeta, getSpecName } from '../utils/clinics';
import { SkeletonClinicGrid, SkeletonDoctorGrid } from '../components/Skeleton';
import { useLang } from '../context/LangContext';

export default function Doctors() {
  const { t, lang } = useLang();
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedClinic, setSelectedClinic] = useState(null);
  const [hoveredClinic, setHoveredClinic] = useState(null);
  const nav = useNavigate();

  useEffect(() => {
    getDoctors().then(setDoctors).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const clinics = {};
  doctors.forEach(doc => {
    const spec = doc.specialization;
    if (!clinics[spec]) clinics[spec] = [];
    clinics[spec].push(doc);
  });

  const clinicDoctors = selectedClinic ? (clinics[selectedClinic] || []) : [];
  const meta = selectedClinic ? getClinicMeta(selectedClinic) : null;
  const clinicName = (spec) => lang === 'ar' ? `${t('clinicPrefix')} ${spec}` : `${getSpecName(spec, lang)} ${t('clinic')}`;
  const clinicDesc = (cm) => lang === 'en' && cm.descEn ? cm.descEn : cm.desc;

  return (
    <div className="fade-up">
      {!selectedClinic ? (
        <>
          {loading ? (
            <SkeletonClinicGrid />
          ) : Object.keys(clinics).length === 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, padding: 48 }}>
              <Search size={28} color="var(--text-muted)" />
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>{t('noClinics')}</p>
            </div>
          ) : (
            <div className="clinic-grid">
              {Object.entries(clinics).map(([spec, docs]) => {
                const cm = getClinicMeta(spec);
                const Icon = cm.icon;
                return (
                  <div key={spec} className="clinic-card"
                    onClick={() => setSelectedClinic(spec)}
                    onMouseEnter={() => setHoveredClinic(spec)}
                    onMouseLeave={() => setHoveredClinic(null)}>
                    <div className="clinic-icon-circle" style={{ background: cm.tint, color: cm.ink }}>
                      <Icon size={26} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 16, fontWeight: 700 }}>{clinicName(spec)}</div>
                      <div className="clinic-badge">{docs.length} {docs.length === 1 ? t('oneDoctor') : t('doctors')}</div>
                    </div>
                    {hoveredClinic === spec && (
                      <div className="clinic-hover-desc">{clinicDesc(cm)}</div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </>
      ) : (
        <>
          <button className="back-btn" onClick={() => setSelectedClinic(null)}>
            <ArrowRight size={16} style={{ transform: lang === 'en' ? 'scaleX(-1)' : 'none' }} />
            {t('allClinics')}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 22 }}>
            <div className="clinic-icon-circle" style={{ background: meta?.tint, color: meta?.ink }}>
              {meta?.icon && <meta.icon size={26} />}
            </div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 700 }}>{clinicName(selectedClinic)}</div>
              <div style={{ fontSize: 13.5, color: 'var(--text-muted)', marginTop: 3 }}>{meta ? clinicDesc(meta) : ''}</div>
            </div>
          </div>

          {loading ? (
            <SkeletonDoctorGrid />
          ) : clinicDoctors.length === 0 ? (
            <div style={{ padding: 48, textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
              {t('noDoctorsInClinic')}
            </div>
          ) : (
            <div className="doctor-grid">
              {clinicDoctors.map(doc => (
                <div key={doc.id} className="doctor-card">
                  <div className="doc-avatar-placeholder">
                    <User size={22} />
                  </div>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ fontSize: 16.5, fontWeight: 700 }}>{doc.name}</div>
                    <div style={{ fontSize: 13, color: 'var(--primary)', fontWeight: 600, marginTop: 4 }}>
                      {getSpecName(doc.specialization, lang)}
                    </div>
                    {doc.bio && (
                      <div style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.65, marginTop: 10 }}>
                        {doc.bio}
                      </div>
                    )}
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16, flexWrap: 'wrap' }}>
                      <button className="btn-primary" style={{ padding: '10px 18px', fontSize: 13.5 }}
                        onClick={() => nav('/book', { state: { doctor: doc } })}>
                        {t('bookNow')}
                      </button>

                      {doc.location_url && (
                        <a href={doc.location_url} target="_blank" rel="noopener noreferrer"
                          className="btn-secondary" style={{
                            padding: '9px 14px', fontSize: 13, display: 'inline-flex',
                            alignItems: 'center', gap: 6, textDecoration: 'none', color: '#D32F2F',
                            background: '#FFEBEE', border: '1px solid #FFCDD2', borderRadius: 8, fontWeight: 600
                          }}>
                          <MapPin size={15} />
                          {lang === 'ar' ? 'موقع العيادة على الخريطة' : 'Clinic Location'}
                        </a>
                      )}

                      <div style={{ fontSize: 12.5, color: 'var(--text-faint)' }}>
                        <span className="online-dot" style={{ width: 6, height: 6 }} /> {t('available')}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
