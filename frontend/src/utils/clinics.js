import { Eye, Smile, HeartPulse, Sparkles, Stethoscope } from 'lucide-react';

export const CLINIC_META = {
  'عيون': {
    icon: Eye,
    nameEn: 'Ophthalmology',
    tint: '#E8F2F0',
    ink: '#1F7A73',
    color: '#1F7A73',
    bg: '#E8F2F0',
    lightBg: '#F4FAF9',
    desc: 'فحص النظر، أمراض الشبكية، وتصحيح الإبصار بالليزر.',
    descEn: 'Eye exams, retina diseases, and laser vision correction.',
  },
  'أسنان': {
    icon: Smile,
    nameEn: 'Dental',
    tint: '#F6EEE1',
    ink: '#A9752F',
    color: '#A9752F',
    bg: '#F6EEE1',
    lightBg: '#FBF6EF',
    desc: 'حشوات، تنظيف وتلميع، تقويم وتجميل الأسنان.',
    descEn: 'Fillings, cleaning, orthodontics and cosmetic dentistry.',
  },
  'باطنة': {
    icon: HeartPulse,
    nameEn: 'Internal Medicine',
    tint: '#E9F0E9',
    ink: '#3F6B4C',
    color: '#3F6B4C',
    bg: '#E9F0E9',
    lightBg: '#F2F7F2',
    desc: 'متابعة الضغط والسكري وأمراض الجهاز الهضمي.',
    descEn: 'Blood pressure, diabetes and digestive system monitoring.',
  },
  'جلدية': {
    icon: Sparkles,
    nameEn: 'Dermatology',
    tint: '#F1ECF3',
    ink: '#6B5580',
    color: '#6B5580',
    bg: '#F1ECF3',
    lightBg: '#F7F4F9',
    desc: 'الأمراض الجلدية المزمنة، الحساسية، وجلسات الليزر.',
    descEn: 'Chronic skin conditions, allergies, and laser sessions.',
  },
};

export const DEFAULT_CLINIC = {
  icon: Stethoscope,
  nameEn: '',
  tint: '#E8F2F0',
  ink: '#1F7A73',
  color: '#6B7280',
  bg: 'rgba(107,114,128,0.1)',
  lightBg: 'rgba(107,114,128,0.05)',
  desc: '',
  descEn: '',
};

export function getClinicMeta(specialization) {
  return CLINIC_META[specialization] || DEFAULT_CLINIC;
}

/** Get display name for a specialization based on language */
export function getSpecName(spec, lang) {
  if (lang === 'en') {
    const meta = CLINIC_META[spec];
    return meta?.nameEn || spec;
  }
  return spec;
}
