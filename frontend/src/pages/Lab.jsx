import { useState } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, FileText, Send } from 'lucide-react';
import { labUploadFile } from '../utils/api';
import { useLang } from '../context/LangContext';

export default function Lab() {
  const { lang } = useLang();
  const [phone, setPhone] = useState('');
  const [testName, setTestName] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!phone.trim()) {
      setMessage({ type: 'error', text: lang === 'ar' ? 'يرجى إدخال رقم هاتف المريض' : 'Please enter patient phone number' });
      return;
    }
    if (!file) {
      setMessage({ type: 'error', text: lang === 'ar' ? 'يرجى اختيار ملف التحليل' : 'Please select a lab report file' });
      return;
    }

    setUploading(true);
    setMessage(null);
    try {
      await labUploadFile(phone.trim(), testName, file);
      setMessage({ type: 'success', text: lang === 'ar' ? 'تم رفع الملف بنجاح ✅' : 'File uploaded successfully ✅' });
      setFile(null);
      setTestName('');
      setPhone('');
    } catch (err) {
      setMessage({
        type: 'error',
        text: typeof err.detail === 'string' ? err.detail : (lang === 'ar' ? 'فشل رفع الملف، تأكد من رقم الهاتف' : 'Upload failed, check phone number')
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fade-up" style={{ maxWidth: 540, margin: '0 auto', paddingBottom: 40 }}>

      {message && (
        <div style={{
          padding: '14px 18px', borderRadius: 12, marginBottom: 20,
          display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, fontWeight: 600,
          background: message.type === 'success' ? '#E8F5E9' : '#FFEBEE',
          color: message.type === 'success' ? '#2E7D32' : '#C62828',
          border: `1px solid ${message.type === 'success' ? '#A5D6A7' : '#EF9A9A'}`
        }}>
          {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span>{message.text}</span>
        </div>
      )}

      <div className="card" style={{ padding: 24 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 20, display: 'flex', alignItems: 'center', gap: 8 }}>
          <UploadCloud size={20} color="var(--primary)" />
          {lang === 'ar' ? 'رفع نتيجة تحليل' : 'Upload Lab Result'}
        </h3>

        <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

          <div>
            <label className="label">{lang === 'ar' ? 'رقم هاتف المريض' : 'Patient Phone Number'}</label>
            <input
              type="text"
              className="input-field"
              placeholder={lang === 'ar' ? '01012345678' : '01012345678'}
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          <div>
            <label className="label">{lang === 'ar' ? 'اسم التحليل (اختياري)' : 'Test Name (optional)'}</label>
            <input
              type="text"
              className="input-field"
              placeholder={lang === 'ar' ? 'مثال: CBC، وظائف كبد...' : 'e.g. CBC, Liver Profile...'}
              value={testName}
              onChange={(e) => setTestName(e.target.value)}
            />
          </div>

          <div>
            <label className="label">{lang === 'ar' ? 'ملف التقرير (PDF, PNG, JPG)' : 'Report File (PDF, PNG, JPG)'}</label>
            <div
              style={{
                border: '2px dashed var(--border-color)', borderRadius: 12, padding: '22px 16px',
                textAlign: 'center', cursor: 'pointer', background: 'var(--bg-body)'
              }}
              onClick={() => document.getElementById('lab-file-input').click()}
            >
              <FileText size={28} color="var(--primary)" style={{ marginBottom: 6 }} />
              <div style={{ fontSize: 13.5, fontWeight: 600 }}>
                {file ? file.name : (lang === 'ar' ? 'اضغط لاختيار الملف' : 'Click to select file')}
              </div>
              {file && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </div>
              )}
              <input
                id="lab-file-input"
                type="file"
                style={{ display: 'none' }}
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => setFile(e.target.files[0])}
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={uploading}
            style={{ padding: '13px', fontSize: 14.5, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
          >
            {uploading ? (
              <>{lang === 'ar' ? 'جاري الرفع...' : 'Uploading...'}</>
            ) : (
              <><Send size={16} /> {lang === 'ar' ? 'رفع التقرير' : 'Upload Report'}</>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
