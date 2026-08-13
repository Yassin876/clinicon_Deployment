export function SkeletonLine({ width = '100%', height = 14, style }) {
  return <div className="skeleton" style={{ width, height, borderRadius: 6, ...style }} />;
}

export function SkeletonCircle({ size = 48 }) {
  return <div className="skeleton" style={{ width: size, height: size, borderRadius: '50%', flexShrink: 0 }} />;
}

export function SkeletonCard({ count = 1 }) {
  return Array.from({ length: count }, (_, i) => (
    <div key={i} className="card" style={{ padding: 24, display: 'flex', alignItems: 'center', gap: 16 }}>
      <SkeletonCircle size={52} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8 }}>
        <SkeletonLine width="60%" height={16} />
        <SkeletonLine width="40%" height={12} />
      </div>
    </div>
  ));
}

export function SkeletonClinicGrid() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16 }}>
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="card" style={{ padding: 32, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
          <div className="skeleton" style={{ width: 72, height: 72, borderRadius: 20 }} />
          <SkeletonLine width="50%" height={18} />
          <SkeletonLine width="80%" height={12} />
          <SkeletonLine width="30%" height={24} style={{ borderRadius: 12 }} />
        </div>
      ))}
    </div>
  );
}

export function SkeletonDoctorGrid() {
  return (
    <div className="doctor-grid">
      {Array.from({ length: 4 }, (_, i) => (
        <div key={i} className="card" style={{ padding: 28, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <div className="skeleton" style={{ width: 72, height: 72, borderRadius: '50%' }} />
          <SkeletonLine width="60%" height={16} />
          <SkeletonLine width="40%" height={12} />
          <SkeletonLine width="100%" height={40} style={{ borderRadius: 12, marginTop: 8 }} />
        </div>
      ))}
    </div>
  );
}
