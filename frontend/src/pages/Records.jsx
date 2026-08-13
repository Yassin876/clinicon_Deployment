import { useEffect, useState } from 'react';
import { uploadFile, getVisits, getMyFiles, getMedications } from '../utils/api';
import { FileText } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useLang } from '../context/LangContext';

export default function Records() {
  const { user } = useAuth();
  const toast = useToast();
  const { t } = useLang();
  const [tab, setTab] = useState('visits');
  const [meds, setMeds] = useState([]);
  const [visits, setVisitsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');
  const [selectedVisit, setSelectedVisit] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [files, setFiles] = useState([]);

  useEffect(() => {
    setLoading(true);
    if (tab === 'meds') getMedications().then(r => setMeds(Array.isArray(r) ? r : r.data || [])).catch(() => setMeds([])).finally(() => setLoading(false));
    else if (tab === 'visits') getVisits().then(r => { const d = r.data || r || []; setVisitsList(d); if (d.length && !selectedVisit) setSelectedVisit(d[0]); }).catch(() => {}).finally(() => setLoading(false));
    else if (tab === 'upload') getMyFiles().then(r => { const d = r.data || r; setFiles(Array.isArray(d) ? d : []); }).catch(() => setFiles([])).finally(() => setLoading(false));
    else setLoading(false);
  }, [tab]);

  const fetchFiles = () => {
    getMyFiles().then(r => { const d = r.data || r; setFiles(Array.isArray(d) ? d : []); }).catch(() => setFiles([]));
  };

  const handleUpload = async (filesToUpload) => {
    if (!filesToUpload?.length) return;
    setUploading(true); setUploadMsg('');
    try {
      for (const f of filesToUpload) await uploadFile(f);
      setUploadMsg(`${filesToUpload.length} ${t('filesUploaded')}`);
      toast(`${filesToUpload.length} ${t('filesUploaded')}`, 'success');
      fetchFiles();
    } catch { setUploadMsg(t('uploadErrorGeneric')); toast(t('uploadError'), 'error'); }
    finally { setUploading(false); setDragOver(false); }
  };

  const TABS = [
    { id: 'meds', label: t('medications') },
    { id: 'visits', label: t('visits') },
    { id: 'upload', label: t('documents') },
  ];

  return (
    <div className="fade-up">
      {/* Tabs */}
      <div className="rec-tabs">
        {TABS.map(({ id, label }) => (
          <button key={id} onClick={() => setTab(id)}
            className={`rec-tab ${tab === id ? 'active' : ''}`}>
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>{t('loading')}</div>
      ) : (
        <>
          {/* Medications — read-only view */}
          {tab === 'meds' && (
            <div className="sphg-card">
              <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--border-light)', fontSize: 15, fontWeight: 700 }}>
                {t('currentMeds')}
              </div>
              {meds.length === 0 ? (
                <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
                  {t('noMeds')}
                </div>
              ) : meds.map((med, i) => (
                <div key={med.id || i} className="med-item">
                  <div className="med-dot" />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 15, fontWeight: 600 }}>{med.medicine_name || med.name}</div>
                    <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 4 }}>
                      {med.frequency || '—'}
                      {med.prescribed_by && <span style={{ marginInlineStart: 8, color: 'var(--primary)', fontSize: 11.5 }}>— {t('prescribedBy')} {med.prescribed_by}</span>}
                    </div>
                  </div>
                  <div className="med-dose-pill">{med.dosage || '—'}</div>
                </div>
              ))}
              <div style={{ padding: '14px 22px', borderTop: '1px solid var(--border-light)', fontSize: 12.5, color: 'var(--text-muted)', textAlign: 'center' }}>
                {t('manageMedsHint')}
              </div>
            </div>
          )}

          {/* Visits */}
          {tab === 'visits' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {visits.length === 0 ? (
                  <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>
                    {t('noVisits')}
                  </div>
                ) : visits.map((v, i) => (
                  <button key={v.id || i}
                    className={`visit-card ${selectedVisit?.id === v.id ? 'selected' : ''}`}
                    onClick={() => setSelectedVisit(v)}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                      <div style={{ fontSize: 15.5, fontWeight: 700 }}>{v.doctor_name || t('visitLabel')}</div>
                      <div style={{ fontSize: 12.5, color: 'var(--text-faint)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                        {v.date || (v.visit_date ? String(v.visit_date).split('T')[0] : (v.created_at ? String(v.created_at).split('T')[0] : '—'))}
                      </div>
                    </div>
                    {v.diagnosis && (
                      <div style={{ fontSize: 13.5, color: 'var(--text-muted)', marginTop: 10, lineHeight: 1.6 }}>
                        {v.diagnosis}
                      </div>
                    )}
                  </button>
                ))}
              </div>

              {/* Visit Detail */}
              {selectedVisit && (
                <div className="sphg-card" style={{ padding: 26, position: 'sticky', top: 110 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontSize: 12.5, color: 'var(--text-faint)', fontWeight: 600 }}>{t('visitDetails')}</div>
                    <div style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      📅 {selectedVisit.date || selectedVisit.visit_date}
                    </div>
                  </div>
                  <div style={{ fontSize: 19, fontWeight: 700, marginTop: 10 }}>👨‍⚕️ {selectedVisit.doctor_name || '—'}</div>
                  <div style={{ height: 1, background: 'var(--border-light)', margin: '18px 0' }} />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                    {selectedVisit.diagnosis && (
                      <div>
                        <div style={{ fontSize: 12, color: 'var(--text-faint)', fontWeight: 700, marginBottom: 6 }}>🩺 {t('diagnosisLabel')}</div>
                        <div style={{ fontSize: 14.5, lineHeight: 1.7, background: 'var(--bg-alt)', padding: 12, borderRadius: 8 }}>{selectedVisit.diagnosis}</div>
                      </div>
                    )}

                    {/* Doctor Notes */}
                    <div>
                      <div style={{ fontSize: 12, color: 'var(--text-faint)', fontWeight: 700, marginBottom: 6 }}>📝 {t('doctorNotes')}</div>
                      <div style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text-secondary)', background: 'var(--bg-alt)', padding: 12, borderRadius: 8, minHeight: 48 }}>
                        {selectedVisit.notes || selectedVisit.doctor_notes || 'لا توجد ملاحظات مدونة لهذه الزيارة'}
                      </div>
                    </div>

                    {/* Prescribed Medications */}
                    <div>
                      <div style={{ fontSize: 12, color: 'var(--text-faint)', fontWeight: 700, marginBottom: 8 }}>💊 الأدوية الـموصوفة في هذه الزيارة</div>
                      {selectedVisit.medications && selectedVisit.medications.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {selectedVisit.medications.map((m, mIdx) => (
                            <div key={m.id || mIdx} style={{
                              padding: '10px 14px', background: 'var(--primary-tint, #e0f2fe)', borderRadius: 8,
                              display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                            }}>
                              <div>
                                <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--primary)' }}>{m.name || m.medicine_name}</div>
                                {m.frequency && <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 2 }}>{m.frequency}</div>}
                              </div>
                              {m.dosage && (
                                <span style={{ fontSize: 11, background: '#fff', padding: '2px 8px', borderRadius: 12, fontWeight: 600 }}>
                                  {m.dosage}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: 13, color: 'var(--text-muted)', background: 'var(--bg-alt)', padding: 12, borderRadius: 8 }}>
                          لم يتم إضافة أدوية في هذه الزيارة
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Upload */}
          {tab === 'upload' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
              <div className={`upload-zone ${dragOver ? 'dragover' : ''}`}
                onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={e => { e.preventDefault(); handleUpload(e.dataTransfer.files); }}>
                <div style={{
                  width: 46, height: 46, margin: '0 auto', borderRadius: 13,
                  background: 'var(--primary-light)', color: 'var(--primary)',
                  display: 'grid', placeItems: 'center', fontSize: 20, fontWeight: 700,
                }}>↑</div>
                <div style={{ fontSize: 16, fontWeight: 700, marginTop: 16 }}>{t('dragFiles')}</div>
                <div style={{ fontSize: 13.5, color: 'var(--text-muted)', marginTop: 8, lineHeight: 1.6 }}>
                  {t('dragFilesSub')}
                </div>
                <label className="btn-primary" style={{ cursor: 'pointer', marginTop: 18, display: 'inline-block' }}>
                  {uploading ? t('uploading') : t('chooseFile')}
                  <input type="file" multiple style={{ display: 'none' }}
                    onChange={e => handleUpload(e.target.files)} disabled={uploading} />
                </label>
                <div style={{ fontSize: 11.5, color: 'var(--text-dim)', marginTop: 14 }}>
                  {t('fileTypes')}
                </div>
                {uploadMsg && (
                  <div style={{ marginTop: 14, fontSize: 13, fontWeight: 600, color: uploadMsg.includes(t('filesUploaded')) ? 'var(--success)' : 'var(--danger)' }}>
                    {uploadMsg}
                  </div>
                )}
              </div>

              <div className="sphg-card">
                <div style={{ padding: '18px 22px', borderBottom: '1px solid var(--border-light)', fontSize: 15, fontWeight: 700 }}>
                  {t('uploadedDocs')}
                </div>
                {files.length === 0 ? (
                  <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                    {t('noFiles')}
                  </div>
                ) : files.map((f, i) => (
                  <div key={f.id || i} style={{
                    padding: '12px 22px', borderBottom: i < files.length - 1 ? '1px solid var(--border-light)' : 'none',
                    display: 'flex', alignItems: 'center', gap: 12,
                  }}>
                    <FileText size={16} style={{ color: 'var(--primary)', flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {f.original_name || f.filename || f.file_name || 'file'}
                      </div>
                      <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 2 }}>
                        {f.created_at ? new Date(f.created_at).toLocaleDateString() : ''}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
