import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { useLang } from './context/LangContext';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Register from './pages/Register';
import Home from './pages/Home';
import Doctors from './pages/Doctors';
import Book from './pages/Book';
import Queue from './pages/Queue';
import Chat from './pages/Chat';
import Records from './pages/Records';
import Medications from './pages/Medications';
import Lab from './pages/Lab';

import ClinicOwner from './pages/ClinicOwner';

// Helper to determine role default landing page
function getRoleDefaultPath(role) {
  if (role === 'doctor') return '/queue';
  if (role === 'clinic_owner') return '/clinic-owner';
  if (role === 'lab') return '/lab';
  return '/';
}

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" replace />;
}

function GuestRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? <Navigate to={getRoleDefaultPath(user.role)} replace /> : children;
}

// Strict Role Guard
function RoleGuard({ allowedRoles, children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to={getRoleDefaultPath(user.role)} replace />;
  }

  return children;
}

function AppLayout() {
  const location = useLocation();
  const { t, lang } = useLang();

  const PAGE_META = {
    '/': { title: t('home'), sub: t('homeSub') },
    '/doctors': { title: t('clinics'), sub: t('clinicsSub') },
    '/book': { title: t('book'), sub: t('bookSub') },
    '/queue': { title: t('queue'), sub: t('queueSub') },
    '/chat': { title: t('assistant'), sub: t('chatSub') },
    '/medications': { title: t('myMedications'), sub: t('medPageSub') },
    '/records': { title: t('records'), sub: t('recordsSub') },
    '/clinic-owner': {
      title: lang === 'ar' ? 'إدارة العيادة' : 'Clinic Management',
      sub: lang === 'ar' ? 'إدارة الدكاترة والمعامل والمعلومات الأساسية' : 'Manage doctors, labs & clinic info'
    },
    '/lab': {
      title: lang === 'ar' ? 'معمل التحاليل' : 'Laboratory Portal',
      sub: lang === 'ar' ? 'رفع وإدارة نتائج تحاليل المرضى' : 'Upload & manage patient lab results'
    },
  };

  const meta = PAGE_META[location.pathname] || PAGE_META['/'];

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-area">
        <header className="app-header">
          <img src="/clinicon-logo.png" alt="Clinicon" className="header-logo-mobile" />
          <div className="app-header-title">
            <h1>{meta.title}</h1>
            <p>{meta.sub}</p>
          </div>
        </header>
        <main className="main-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<GuestRoute><Login /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><Register /></GuestRoute>} />
      
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        {/* Patient Routes */}
        <Route path="/" element={<RoleGuard allowedRoles={['patient', 'doctor']}><Home /></RoleGuard>} />
        <Route path="/doctors" element={<RoleGuard allowedRoles={['patient']}><Doctors /></RoleGuard>} />
        <Route path="/book" element={<RoleGuard allowedRoles={['patient']}><Book /></RoleGuard>} />
        <Route path="/chat" element={<RoleGuard allowedRoles={['patient']}><Chat /></RoleGuard>} />
        <Route path="/medications" element={<RoleGuard allowedRoles={['patient']}><Medications /></RoleGuard>} />
        <Route path="/records" element={<RoleGuard allowedRoles={['patient']}><Records /></RoleGuard>} />

        {/* Shared Patient, Doctor & Clinic Owner Routes */}
        <Route path="/queue" element={<RoleGuard allowedRoles={['patient', 'doctor', 'clinic_owner']}><Queue /></RoleGuard>} />

        {/* Clinic Owner Routes */}
        <Route path="/clinic-owner" element={<RoleGuard allowedRoles={['clinic_owner']}><ClinicOwner /></RoleGuard>} />

        {/* Laboratory Routes */}
        <Route path="/lab" element={<RoleGuard allowedRoles={['lab']}><Lab /></RoleGuard>} />

        {/* Catch-all redirect - blocks invalid routes */}
        <Route path="*" element={<Navigate to={user ? getRoleDefaultPath(user.role) : '/login'} replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
