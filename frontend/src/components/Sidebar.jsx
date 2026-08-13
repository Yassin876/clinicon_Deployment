import { NavLink } from 'react-router-dom';
import { Home, Building2, CalendarPlus, Clock, MessageSquare, FileText, LogOut, Sun, Moon, Globe, Settings, Menu, X, Pill, FlaskConical } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLang } from '../context/LangContext';
import { useState } from 'react';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { dark, toggle: toggleTheme } = useTheme();
  const { lang, toggle: toggleLang, t } = useLang();
  const displayName = getDisplayName(user, t);
  const initial = displayName.charAt(0) || '؟';
  const [mobileOpen, setMobileOpen] = useState(false);

  const isDoctor = user?.role === 'doctor';
  const isClinicOwner = user?.role === 'clinic_owner';
  const isLab = user?.role === 'lab';
  const isPatient = user?.role === 'patient' || (!isDoctor && !isLab && !isClinicOwner);

  let NAV_ITEMS = [];

  if (isClinicOwner) {
    NAV_ITEMS = [
      { to: '/clinic-owner', icon: Building2, label: lang === 'ar' ? 'إدارة العيادة' : 'Clinic Management' },
      { to: '/queue', icon: Clock, label: t('queue') },
    ];
  } else if (isLab) {
    NAV_ITEMS = [
      { to: '/lab', icon: FlaskConical, label: lang === 'ar' ? 'معمل التحاليل' : 'Lab Portal' },
    ];
  } else if (isDoctor) {
    // Doctor only sees Queue (their patient list)
    NAV_ITEMS = [
      { to: '/queue', icon: Clock, label: lang === 'ar' ? 'الطابور' : 'Queue' },
    ];
  } else {
    // Patient
    NAV_ITEMS = [
      { to: '/', icon: Home, label: t('home'), end: true },
      { to: '/doctors', icon: Building2, label: t('clinics') },
      { to: '/book', icon: CalendarPlus, label: t('book') },
      { to: '/queue', icon: Clock, label: t('queue') },
      { to: '/chat', icon: MessageSquare, label: t('assistant') },
      { to: '/medications', icon: Pill, label: t('myMedications') },
      { to: '/records', icon: FileText, label: t('records') },
    ];
  }

  // Mobile bottom nav
  const BOTTOM_NAV = NAV_ITEMS.slice(0, 5);

  return (
    <>
      {/* Desktop Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <img src="/clinicon-logo.png" alt="Clinicon" className="sidebar-logo" />
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
              <div className="sidebar-link-card">
                <Icon size={18} />
                <span>{label}</span>
              </div>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <button onClick={toggleTheme} className="sidebar-theme-btn" title={dark ? t('lightMode') : t('darkMode')}>
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <button onClick={toggleLang} className="sidebar-theme-btn" title="Language">
              <Globe size={16} />
              <span>{lang === 'ar' ? 'EN' : 'عربي'}</span>
            </button>
          </div>
          <div className="sidebar-user">
            <div className="sidebar-avatar">{initial}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                fontSize: 13.5, fontWeight: 600, color: 'var(--text)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>{displayName}</p>
            </div>
            <button onClick={logout} title={t('logout')}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--text-muted)', padding: 6, borderRadius: 8,
                transition: 'color .15s', display: 'flex', alignItems: 'center',
              }}
              onMouseEnter={e => e.currentTarget.style.color = 'var(--danger)'}
              onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}>
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile Bottom Nav */}
      <nav className="mobile-bottom-nav">
        {BOTTOM_NAV.map(({ to, icon: Icon, label, end }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => `mobile-nav-item ${isActive ? 'active' : ''}`}>
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
        <button className="mobile-nav-item" onClick={() => setMobileOpen(true)}>
          <Menu size={20} />
          <span>{t('more') || 'المزيد'}</span>
        </button>
      </nav>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="mobile-drawer-overlay" onClick={() => setMobileOpen(false)}>
          <div className="mobile-drawer" onClick={e => e.stopPropagation()}>
            <div className="mobile-drawer-header">
              <img src="/clinicon-logo.png" alt="Clinicon" style={{ height: 32, objectFit: 'contain' }} />
              <button onClick={() => setMobileOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', padding: 4 }}>
                <X size={22} />
              </button>
            </div>
            <div className="mobile-drawer-user">
              <div className="sidebar-avatar">{initial}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>{displayName}</p>
              </div>
            </div>
            {/* Extra nav items not in bottom bar */}
            {!isDoctor && !isClinicOwner && !isLab && (
              <NavLink to="/records" className="mobile-drawer-link" onClick={() => setMobileOpen(false)}>
                <FileText size={18} /> {t('records')}
              </NavLink>
            )}
            <div className="mobile-drawer-actions">
              <button onClick={toggleTheme} className="sidebar-theme-btn">
                {dark ? <Sun size={16} /> : <Moon size={16} />}
                <span>{dark ? t('lightMode') : t('darkMode')}</span>
              </button>
              <button onClick={toggleLang} className="sidebar-theme-btn">
                <Globe size={16} />
                <span>{lang === 'ar' ? 'EN' : 'عربي'}</span>
              </button>
            </div>
            <button onClick={() => { logout(); setMobileOpen(false); }} className="mobile-drawer-logout">
              <LogOut size={16} /> {t('logout')}
            </button>
          </div>
        </div>
      )}
    </>
  );
}

function getDisplayName(user, t) {
  const raw = user?.name || user?.full_name || '';
  if (!raw || raw.includes('@') || /^[a-zA-Z0-9._-]+$/.test(raw)) return t('user');
  return raw;
}
