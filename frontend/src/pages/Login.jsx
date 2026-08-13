import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { login } from '../utils/api';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LangContext';

export default function Login() {
  const { t, lang } = useLang();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { loginUser } = useAuth();
  const nav = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const data = await login(email, password);
      loginUser({
        id: data.user_id,
        name: data.full_name,
        email: data.email,
        role: data.role,
        doctor_id: data.doctor_id,
      }, data.access_token);
      nav('/');
    } catch (err) {
      const d = err.detail;
      setError(
        typeof d === 'string' ? d :
        Array.isArray(d) ? d.map(e => e.msg || e).join(' ، ') :
        err.error || t('loginError')
      );
    } finally { setLoading(false); }
  };

  const features = [t('feature1'), t('feature2'), t('feature3')];

  return (
    <div className="auth-page">
      {/* Left: Branding */}
      <div className="auth-side">
        <div className="auth-dots" />
        <div style={{ position: 'relative', zIndex: 1, textAlign: 'center', maxWidth: 400 }}>
          <img src="/clinicon-logo.png" alt="Clinicon"
            style={{ height: 64, marginBottom: 24, filter: 'brightness(0) invert(1) brightness(0.95)' }} />

          <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12, color: '#EAF2F0' }}>
            Clinicon
          </h1>
          <p style={{ fontSize: 15, color: 'rgba(234,242,240,0.7)', lineHeight: 1.9, marginBottom: 40 }}>
            {t('brandDesc')}
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, textAlign: 'start' }}>
            {features.map(feat => (
              <div key={feat} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 14px', borderRadius: 10,
                background: 'rgba(234,242,240,.04)', border: '1px solid rgba(234,242,240,.06)',
                fontSize: 13.5, color: 'rgba(234,242,240,0.85)',
              }}>
                <span style={{ color: '#1F7A73', fontWeight: 700 }}>✓</span>
                {feat}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Form */}
      <div className="auth-form-side">
        <div className="auth-form">
          <div style={{ marginBottom: 36 }}>
            <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>{t('welcome')}</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 13.5, lineHeight: 1.7 }}>
              {t('loginSub')}
            </p>
          </div>

          {error && <div className="error-box" style={{ marginBottom: 20 }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 20 }}>
              <label className="label">{t('email')}</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                required placeholder="example@mail.com" className="input-field"
                style={{ direction: 'ltr', textAlign: lang === 'ar' ? 'right' : 'left' }} />
            </div>
            <div style={{ marginBottom: 32 }}>
              <label className="label">{t('password')}</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                required placeholder="••••••••" className="input-field" />
            </div>
            <button type="submit" disabled={loading} className="btn-primary"
              style={{ width: '100%', padding: 14, fontSize: 15 }}>
              {loading ? t('loggingIn') : t('login')}
            </button>
          </form>

          <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-muted)', marginTop: 28 }}>
            {t('noAccount')}{' '}
            <Link to="/register" style={{ color: 'var(--primary)', fontWeight: 700, textDecoration: 'none' }}>
              {t('registerHere')}
            </Link>
          </p>

          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            justifyContent: 'center', marginTop: 40,
            color: 'var(--text-muted)', fontSize: 12,
          }}>
            <Shield size={14} /> {t('secureData')}
          </div>
        </div>
      </div>
    </div>
  );
}
