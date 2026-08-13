import { useEffect, useState } from 'react';
import { Pill, Clock, Trash2, Plus, Send, Edit3 } from 'lucide-react';
import { getMedications, addMedication, deleteMedication, addMedReminders, linkTelegram, getTelegramStatus, getTelegramLinkUrl, updateMedication } from '../utils/api';
import { useToast } from '../context/ToastContext';
import { useLang } from '../context/LangContext';

const PERIODS = [
  { id: 'empty_stomach', time: '06:00' },
  { id: 'before_breakfast', time: '07:00' },
  { id: 'after_breakfast', time: '08:00' },
  { id: 'before_lunch', time: '13:00' },
  { id: 'after_lunch', time: '14:00' },
  { id: 'before_dinner', time: '19:00' },
  { id: 'after_dinner', time: '20:00' },
  { id: 'before_sleep', time: '22:00' },
];

export default function Medications() {
  const toast = useToast();
  const { t } = useLang();
  const [meds, setMeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newMed, setNewMed] = useState({ name: '', dosage: '', frequency: '' });
  const [saving, setSaving] = useState(false);

  // Reminder scheduling state
  const [selectedMed, setSelectedMed] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [periodTime, setPeriodTime] = useState('');
  const [addingReminder, setAddingReminder] = useState(false);

  // Edit state
  const [editingMed, setEditingMed] = useState(null);
  const [editForm, setEditForm] = useState({});

  // Telegram state
  const [telegramStatus, setTelegramStatus] = useState(null);
  const [chatIdInput, setChatIdInput] = useState('');
  const [linkingTg, setLinkingTg] = useState(false);
  const [botLink, setBotLink] = useState('');
  const [waitingForLink, setWaitingForLink] = useState(false);

  useEffect(() => {
    getMedications().then(setMeds).catch(() => {}).finally(() => setLoading(false));
    getTelegramStatus().then(setTelegramStatus).catch(() => {});
    getTelegramLinkUrl().then(r => setBotLink(r.link)).catch(() => {});
  }, []);

  // Auto-check if telegram got linked after user clicked the bot link
  useEffect(() => {
    if (!waitingForLink) return;
    const interval = setInterval(() => {
      getTelegramStatus().then(s => {
        if (s.linked) {
          setTelegramStatus(s);
          setWaitingForLink(false);
          toast(t('telegramSaved'), 'success');
        }
      }).catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [waitingForLink]);

  const periodLabel = (id) => {
    const map = {
      empty_stomach: t('onEmptyStomach'),
      before_breakfast: t('beforeBreakfast'),
      after_breakfast: t('afterBreakfast'),
      before_lunch: t('beforeLunch'),
      after_lunch: t('afterLunch'),
      before_dinner: t('beforeDinner'),
      after_dinner: t('afterDinner'),
      before_sleep: t('beforeSleep'),
    };
    return map[id] || id;
  };

  const handleAddMed = async (e) => {
    e.preventDefault();
    if (!newMed.name.trim() || !newMed.dosage.trim() || !newMed.frequency) { toast(t('medRequired'), 'error'); return; }
    setSaving(true);
    try {
      await addMedication(newMed.name, newMed.dosage, newMed.frequency);
      setNewMed({ name: '', dosage: '', frequency: '' });
      setMeds(await getMedications());
      toast(t('medAdded'), 'success');
    } catch { toast(t('medAddError'), 'error'); }
    finally { setSaving(false); }
  };

  const handleDeleteMed = async (id) => {
    try {
      await deleteMedication(id);
      setMeds(m => m.filter(med => (med.id || med._id) !== id));
      if (selectedMed?.id === id) setSelectedMed(null);
      toast(t('medDeleted'), 'success');
    } catch { toast(t('medDeleteError'), 'error'); }
  };

  const handleAddReminder = async () => {
    if (!selectedMed || !periodTime) return;
    setAddingReminder(true);
    try {
      await addMedReminders(selectedMed.id, [{ reminder_time: periodTime + ':00', is_active: true }]);
      // Refresh meds to get updated reminders
      const updated = await getMedications();
      setMeds(updated);
      setSelectedMed(updated.find(m => m.id === selectedMed.id) || null);
      setPeriodTime('');
      setSelectedPeriod('');
      toast(t('reminderSaved'), 'success');
    } catch { toast(t('errorOccurred'), 'error'); }
    finally { setAddingReminder(false); }
  };

  const handleLinkTelegram = async (e) => {
    e.preventDefault();
    if (!chatIdInput.trim()) return;
    setLinkingTg(true);
    try {
      await linkTelegram(parseInt(chatIdInput));
      setTelegramStatus({ linked: true, chat_id: parseInt(chatIdInput), notif_enabled: true });
      setChatIdInput('');
      toast(t('telegramSaved'), 'success');
    } catch { toast(t('errorOccurred'), 'error'); }
    finally { setLinkingTg(false); }
  };

  const handleEditMed = async (e) => {
    e.preventDefault();
    try {
      await updateMedication(editingMed.id, editForm);
      setEditingMed(null);
      const updated = await getMedications();
      setMeds(updated);
      if (selectedMed?.id === editingMed.id) setSelectedMed(updated.find(m => m.id === editingMed.id) || null);
      toast(t('medUpdated'), 'success');
    } catch { toast(t('errorOccurred'), 'error'); }
  };

  const handleSelectPeriod = (p) => {
    setSelectedPeriod(p.id);
    setPeriodTime(p.time);
  };

  return (
    <div className="fade-up">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 18, alignItems: 'start' }}>

        {/* ═══ Left: Medication List + Add ═══ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Add Med Form */}
          <div className="sphg-card" style={{ padding: 22 }}>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Pill size={16} style={{ color: 'var(--primary)' }} />
              {t('addNewMed')}
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginBottom: 16 }}>{t('addMedSub')}</div>
            <form onSubmit={handleAddMed} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <input value={newMed.name} onChange={e => setNewMed({ ...newMed, name: e.target.value })}
                placeholder={t('medName')} className="input-field" style={{ borderRadius: 10, padding: '11px 14px', fontSize: 14 }} />
              <input value={newMed.dosage} onChange={e => setNewMed({ ...newMed, dosage: e.target.value })}
                placeholder={t('dosage')} className="input-field" style={{ borderRadius: 10, padding: '11px 14px', fontSize: 14 }} />
              <input value={newMed.frequency} onChange={e => setNewMed({ ...newMed, frequency: e.target.value.replace(/[^0-9]/g, '') })}
                placeholder={t('frequencyNum')} className="input-field" type="number" min="1" max="10"
                style={{ borderRadius: 10, padding: '11px 14px', fontSize: 14 }} />
              <button type="submit" disabled={saving} className="btn-primary" style={{ width: '100%', padding: 11 }}>
                {saving ? t('saving') : t('saveMed')}
              </button>
            </form>
          </div>

          {/* Med List */}
          <div className="sphg-card">
            <div style={{ padding: '16px 22px', borderBottom: '1px solid var(--border-light)', fontSize: 15, fontWeight: 700 }}>
              {t('currentMeds')}
            </div>
            {loading ? (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)' }}>{t('loading')}</div>
            ) : meds.length === 0 ? (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--text-muted)', fontSize: 14 }}>{t('noMeds')}</div>
            ) : meds.map((med, i) => (
              <div key={med.id || i}
                style={{
                  padding: '14px 22px', borderBottom: i < meds.length - 1 ? '1px solid var(--border-light)' : 'none',
                  display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer',
                  background: selectedMed?.id === med.id ? 'var(--primary-light)' : 'transparent',
                  transition: 'background .15s',
                }}
                onClick={() => setSelectedMed(selectedMed?.id === med.id ? null : med)}>
                <div className="med-dot" />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 14.5, fontWeight: 600 }}>{med.medicine_name || med.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>
                    {med.dosage || '—'} · {med.frequency ? `${med.frequency} ${t('timesDaily')}` : '—'}
                    {med.prescribed_by_name && <span style={{ marginInlineStart: 6, color: 'var(--primary)', fontSize: 11 }}>— {t('prescribedBy')} {med.prescribed_by_name}</span>}
                  </div>
                  {med.reminders?.length > 0 && (
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                      {med.reminders.filter(r => r.is_active).map((r, j) => (
                        <span key={j} style={{
                          fontSize: 11, padding: '2px 8px', borderRadius: 6,
                          background: 'var(--primary-light)', color: 'var(--primary)', fontWeight: 600,
                          fontFamily: 'var(--font-mono)',
                        }}>
                          <Clock size={10} style={{ marginInlineEnd: 3 }} />
                          {r.reminder_time?.slice(0, 5)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <button className="med-delete-btn" title={t('editMed')} style={{ color: 'var(--text-muted)' }}
                  onClick={(e) => { e.stopPropagation(); setEditingMed(med); setEditForm({ medicine_name: med.medicine_name || med.name, dosage: med.dosage, frequency: med.frequency }); }}>
                  <Edit3 size={14} />
                </button>
                <button className="med-delete-btn" title={t('delete')}
                  onClick={(e) => { e.stopPropagation(); handleDeleteMed(med.id || med._id); }}>
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* ═══ Right: Scheduling + Telegram ═══ */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          {/* Schedule Reminders */}
          <div className="sphg-card" style={{ padding: 22 }}>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Clock size={16} style={{ color: 'var(--primary)' }} />
              {t('medTiming')}
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginBottom: 16 }}>
              {t('reminderWillSend')}
            </div>

            {!selectedMed ? (
              <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, border: '2px dashed var(--border-light)', borderRadius: 12 }}>
                {t('choosePeriod')} — {t('noReminders')}
              </div>
            ) : (() => {
              const requiredCount = parseInt(selectedMed.frequency) || 0;
              const activeReminders = (selectedMed.reminders || []).filter(r => r.is_active);
              const currentCount = activeReminders.length;
              const isFull = requiredCount > 0 && currentCount >= requiredCount;
              const isComplete = requiredCount > 0 && currentCount === requiredCount;

              return (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--primary)' }}>
                  {selectedMed.medicine_name || selectedMed.name} — {selectedMed.dosage}
                </div>

                {/* Progress indicator */}
                {requiredCount > 0 && (
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
                    background: isComplete ? 'var(--success-light, #e8f5e9)' : 'var(--primary-light)',
                    borderRadius: 10, marginBottom: 14,
                    fontSize: 13, fontWeight: 600,
                    color: isComplete ? 'var(--success, #2e7d32)' : 'var(--primary)',
                  }}>
                    {isComplete ? '✓' : '⏳'} {t('remindersProgress')}: {currentCount} / {requiredCount}
                    {isComplete && <span style={{ marginInlineStart: 'auto', fontSize: 11.5 }}>{t('allRemindersSet')}</span>}
                  </div>
                )}

                {/* Period Buttons — hidden when full */}
                {!isFull && (
                  <>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
                      {PERIODS.map(p => (
                        <button key={p.id}
                          onClick={() => handleSelectPeriod(p)}
                          style={{
                            padding: '8px 14px', borderRadius: 10, fontSize: 12.5, fontWeight: 600,
                            border: selectedPeriod === p.id ? '2px solid var(--primary)' : '1.5px solid var(--border-light)',
                            background: selectedPeriod === p.id ? 'var(--primary-light)' : 'var(--card)',
                            color: selectedPeriod === p.id ? 'var(--primary)' : 'var(--text-secondary)',
                            cursor: 'pointer', transition: 'all .15s',
                          }}>
                          {periodLabel(p.id)}
                        </button>
                      ))}
                    </div>

                    {/* Time picker + Add */}
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      <label style={{ fontSize: 13, fontWeight: 600, flexShrink: 0 }}>{t('periodTime')}:</label>
                      <input type="time" value={periodTime} onChange={e => setPeriodTime(e.target.value)}
                        className="input-field" style={{ flex: 1, padding: '10px 12px' }} />
                      <button className="btn-primary" disabled={!periodTime || addingReminder}
                        style={{ padding: '10px 18px', fontSize: 13 }}
                        onClick={handleAddReminder}>
                        <Plus size={14} /> {addingReminder ? t('saving') : t('addPeriod')}
                      </button>
                    </div>
                  </>
                )}

                {/* Current reminders for this med */}
                {activeReminders.length > 0 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700, color: 'var(--text-faint)', marginBottom: 8 }}>{t('currentReminders')}</div>
                    {activeReminders.map((r, j) => (
                      <div key={j} style={{
                        display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px',
                        background: 'var(--card)', border: '1px solid var(--border-light)',
                        borderRadius: 8, marginBottom: 6,
                      }}>
                        <Clock size={14} style={{ color: 'var(--primary)' }} />
                        <span style={{ fontSize: 14, fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>
                          {r.reminder_time?.slice(0, 5)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </>
              );
            })()}
          </div>

          {/* Telegram Link */}
          <div className="sphg-card" style={{ padding: 22 }}>
            <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Send size={16} style={{ color: '#0088cc' }} />
              Telegram
            </div>
            {telegramStatus?.linked ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 10 }}>
                <span className="online-dot" style={{ width: 8, height: 8 }} />
                <span style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--success)' }}>{t('telegramLinked')}</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  ID: {telegramStatus.chat_id}
                </span>
              </div>
            ) : (
              <>
                <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginBottom: 12, marginTop: 4 }}>
                  {t('telegramNotLinked')}
                </div>

                {/* زرار ابدأ مع البوت */}
                {botLink && (
                  <a href={botLink} target="_blank" rel="noopener noreferrer"
                    onClick={() => setWaitingForLink(true)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                      padding: '12px 20px', borderRadius: 12, fontSize: 14, fontWeight: 700,
                      background: '#0088cc', color: '#fff', textDecoration: 'none',
                      transition: 'opacity .15s', marginBottom: 12,
                    }}
                    onMouseEnter={e => e.currentTarget.style.opacity = '0.85'}
                    onMouseLeave={e => e.currentTarget.style.opacity = '1'}>
                    <Send size={16} />
                    {t('startWithBot')}
                  </a>
                )}

                {waitingForLink && (
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
                    background: 'var(--primary-light)', borderRadius: 10, marginBottom: 12,
                    fontSize: 12.5, color: 'var(--primary)', fontWeight: 600,
                  }}>
                    <span className="loading-spinner" style={{ width: 14, height: 14 }} />
                    {t('waitingForTelegram')}
                  </div>
                )}

                {/* Manual fallback */}
                <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginBottom: 8 }}>
                  {t('orEnterManually')}
                </div>
                <form onSubmit={handleLinkTelegram} style={{ display: 'flex', gap: 8 }}>
                  <input value={chatIdInput} onChange={e => setChatIdInput(e.target.value)}
                    placeholder={t('telegramId')} className="input-field"
                    style={{ flex: 1, padding: '10px 12px' }} type="number" />
                  <button type="submit" disabled={linkingTg} className="btn-primary" style={{ padding: '10px 16px', fontSize: 13 }}>
                    {linkingTg ? t('saving') : t('linkTelegram')}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Edit Medication Modal */}
      {editingMed && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', display: 'grid', placeItems: 'center', zIndex: 999 }}
          onClick={() => setEditingMed(null)}>
          <div className="sphg-card" style={{ padding: 26, width: '90%', maxWidth: 420 }} onClick={e => e.stopPropagation()}>
            <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 18 }}>{t('editMed')}</div>
            <form onSubmit={handleEditMed} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input value={editForm.medicine_name || ''} onChange={e => setEditForm({ ...editForm, medicine_name: e.target.value })}
                placeholder={t('medName')} className="input-field" style={{ borderRadius: 10, padding: '11px 14px' }} />
              <input value={editForm.dosage || ''} onChange={e => setEditForm({ ...editForm, dosage: e.target.value })}
                placeholder={t('dosage')} className="input-field" style={{ borderRadius: 10, padding: '11px 14px' }} />
              <input value={editForm.frequency || ''} onChange={e => setEditForm({ ...editForm, frequency: e.target.value.replace(/[^0-9]/g, '') })}
                placeholder={t('frequencyNum')} className="input-field" type="number" min="1" max="10"
                style={{ borderRadius: 10, padding: '11px 14px' }} />
              <div style={{ display: 'flex', gap: 10 }}>
                <button type="submit" className="btn-primary" style={{ flex: 1, padding: 12 }}>{t('save')}</button>
                <button type="button" className="btn-secondary" onClick={() => setEditingMed(null)}>{t('cancel')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
