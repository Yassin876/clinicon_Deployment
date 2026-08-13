import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2, CalendarPlus, Clock, MessageSquare, FileText,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LangContext';
import { getDoctors, getQueue } from '../utils/api';
import { Settings } from 'lucide-react';

export default function Home() {
  const { user } = useAuth();
  const { t, lang } = useLang();
  const [doctors, setDoctors] = useState([]);
  const [queue, setQueue] = useState([]);
  const [hoveredTile, setHoveredTile] = useState(null);

  useEffect(() => {
    getDoctors().then(setDoctors).catch(() => {});
    getQueue().then(r => setQueue(r.data || r || [])).catch(() => {});
  }, []);

  const displayName = getDisplayName(user, t);
  const hour = new Date().getHours();
  const greeting = hour < 12 ? t('goodMorning') : t('goodEvening');

  const clinicCount = new Set(doctors.map(d => d.specialization)).size;
  const waiting = queue.filter(q => q.status === 'waiting').length;
  const current = queue.find(q => q.isCurrent);

  const isAdmin = user?.role === 'admin';

  const TILES = isAdmin
    ? [
        { to: '/doctors', icon: Building2, title: t('browseClinics'), desc: `${clinicCount} ${t('specs')} · ${doctors.length} ${t('doctors')}` },
        { to: '/queue', icon: Clock, title: t('liveQueue'), desc: t('queueSub') },
        { to: '/admin', icon: Settings, title: t('admin'), desc: t('adminSub') },
      ]
    : [
        { to: '/doctors', icon: Building2, title: t('browseClinics'), desc: `${clinicCount} ${t('specs')} · ${doctors.length} ${t('doctors')}` },
        { to: '/book', icon: CalendarPlus, title: t('bookAppointment'), desc: t('bookSub') },
        { to: '/queue', icon: Clock, title: t('liveQueue'), desc: t('queueSub') },
        { to: '/chat', icon: MessageSquare, title: t('smartAssistant'), desc: t('chatSub') },
        { to: '/records', icon: FileText, title: t('myRecords'), desc: t('recordsSub') },
      ];

  const topTiles = TILES.slice(0, 3);
  const bottomTiles = TILES.slice(3);
  const locale = lang === 'ar' ? 'ar-EG' : 'en-US';

  return (
    <div className="fade-up">
      <div className="home-hero">
        <div className="home-hero-content">
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, color: 'rgba(234,242,240,0.65)', fontWeight: 600, marginBottom: 10 }}>
              {new Date().toLocaleDateString(locale, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
            </div>
            <h2>{greeting}{lang === 'ar' ? ' يا ' : ', '}{displayName}</h2>
            <p>{t('heroSub')}</p>
            <div className="home-hero-actions">
              {isAdmin ? (
                <>
                  <Link to="/admin" className="btn-hero-primary" style={{ textDecoration: 'none' }}>{t('admin')}</Link>
                  <Link to="/queue" className="btn-hero-secondary" style={{ textDecoration: 'none' }}>{t('liveQueue')}</Link>
                </>
              ) : (
                <>
                  <Link to="/book" className="btn-hero-primary" style={{ textDecoration: 'none' }}>{t('bookNow')}</Link>
                  <Link to="/chat" className="btn-hero-secondary" style={{ textDecoration: 'none' }}>{t('askAssistant')}</Link>
                </>
              )}
            </div>
          </div>
          <div className="hero-brand-badge">
            <img src="/clinicon-icon.svg" alt="" className="hero-brand-icon" />
            <span className="hero-brand-name">Clinicon</span>
          </div>
        </div>
      </div>

      <div className="home-stats">
        <div className="stat-card dark">
          <div className="stat-card-label">{t('servingNow')}</div>
          <div className="stat-card-value">{current?.queueNumber || '—'}</div>
          <div className="stat-card-sub">{current?.name || '—'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">{t('waiting')}</div>
          <div className="stat-card-value">{waiting}</div>
          <div className="stat-card-sub">{waiting > 0 ? `~${waiting * 15} ${t('minutes')}` : '—'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">{t('availableSpecs')}</div>
          <div className="stat-card-value">{clinicCount}</div>
          <div className="stat-card-sub">{doctors.length} {t('doctors')}</div>
        </div>
      </div>

      <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>{t('quickActions')}</div>
      {/* Desktop: split into rows of 3 + 2 centered */}
      <div className="quick-tiles-desktop">
        <div className="quick-tiles-row">
          {topTiles.map(({ to, icon: Icon, title, desc }) => (
            <Link key={to} to={to} className="quick-tile"
              onMouseEnter={() => setHoveredTile(to)} onMouseLeave={() => setHoveredTile(null)}>
              <div className="quick-tile-icon"><Icon size={20} /></div>
              <h3>{title}</h3>
              {hoveredTile === to && <p className="quick-tile-desc">{desc}</p>}
            </Link>
          ))}
        </div>
        <div className="quick-tiles-row centered">
          {bottomTiles.map(({ to, icon: Icon, title, desc }) => (
            <Link key={to} to={to} className="quick-tile"
              onMouseEnter={() => setHoveredTile(to)} onMouseLeave={() => setHoveredTile(null)}>
              <div className="quick-tile-icon"><Icon size={20} /></div>
              <h3>{title}</h3>
              {hoveredTile === to && <p className="quick-tile-desc">{desc}</p>}
            </Link>
          ))}
        </div>
      </div>
      {/* Mobile: single flat grid */}
      <div className="quick-tiles-mobile">
        {TILES.map(({ to, icon: Icon, title, desc }) => (
          <Link key={to} to={to} className="quick-tile"
            onMouseEnter={() => setHoveredTile(to)} onMouseLeave={() => setHoveredTile(null)}>
            <div className="quick-tile-icon"><Icon size={20} /></div>
            <h3>{title}</h3>
            {hoveredTile === to && <p className="quick-tile-desc">{desc}</p>}
          </Link>
        ))}
      </div>
    </div>
  );
}

function getDisplayName(user, t) {
  const raw = user?.name || user?.full_name || '';
  if (!raw || raw.includes('@') || /^[a-zA-Z0-9._-]+$/.test(raw)) return t('user');
  return raw.split(' ')[0];
}
