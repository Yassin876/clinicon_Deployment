import { useState, useRef, useEffect } from 'react';
import { Send, RotateCcw, MessageSquare, Plus, Trash2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLang } from '../context/LangContext';

const getSuggestions = (t) => [
  t('suggestion1'),
  t('suggestion2'),
  t('suggestion3'),
  t('suggestion4'),
];

export default function Chat() {
  const { user } = useAuth();
  const { t, lang } = useLang();
  const [messages, setMessages] = useState([
    { role: 'bot', text: t('chatWelcome') },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  const sentContext = useRef(false);

  // Chat history state
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('clinicon-chat-history');
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [activeChat, setActiveChat] = useState(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  // Save current conversation to history when it has user messages
  const saveToHistory = (msgs) => {
    const userMsgs = msgs.filter(m => m.role === 'user');
    if (userMsgs.length === 0) return;
    const title = userMsgs[0].text.slice(0, 40) + (userMsgs[0].text.length > 40 ? '…' : '');
    const entry = {
      id: activeChat || Date.now().toString(),
      title,
      messages: msgs,
      date: new Date().toLocaleDateString(lang === 'ar' ? 'ar-EG' : 'en-US', { day: 'numeric', month: 'short' }),
    };
    setHistory(prev => {
      const filtered = prev.filter(h => h.id !== entry.id);
      const updated = [entry, ...filtered].slice(0, 20);
      try { localStorage.setItem('clinicon-chat-history', JSON.stringify(updated)); } catch {}
      return updated;
    });
    if (!activeChat) setActiveChat(entry.id);
  };

  const displayName = getDisplayName(user);
  const initial = displayName.charAt(0) || '؟';

  const send = async (text) => {
    const userMsg = (text || input).trim();
    if (!userMsg || loading) return;
    setInput('');
    const newMsgs = [...messages, { role: 'user', text: userMsg }];
    setMessages(newMsgs);
    setLoading(true);
    try {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 300000);
      const sessionId = user?.user_id || user?.id || 'anon';
      const body = { message: userMsg, session_id: sessionId };
      if (user && !sentContext.current) {
        body.user_name = user.name || user.full_name || '';
        body.user_email = user.email || '';
        sentContext.current = true;
      }
      const res = await fetch('/agent/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      const data = await res.json();
      const reply = data.reply || t('chatErrorReply');
      const finalMsgs = [...newMsgs, { role: 'bot', text: reply }];
      setMessages(finalMsgs);
      saveToHistory(finalMsgs);
    } catch (err) {
      const txt = err.name === 'AbortError'
        ? t('chatErrorTimeout')
        : t('chatErrorConnection');
      const finalMsgs = [...newMsgs, { role: 'bot', text: txt }];
      setMessages(finalMsgs);
      saveToHistory(finalMsgs);
    } finally { setLoading(false); }
  };

  const startNewChat = async () => {
    const sessionId = user?.user_id || user?.id || 'anon';
    try {
      await fetch('/agent/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch {}
    sentContext.current = false;
    setActiveChat(null);
    setMessages([{ role: 'bot', text: t('chatWelcomeNew') }]);
  };

  const loadChat = async (entry) => {
    // Reset agent state so it doesn't carry over from a different conversation
    const sessionId = user?.user_id || user?.id || 'anon';
    try {
      await fetch('/agent/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch {}
    sentContext.current = false;
    setActiveChat(entry.id);
    setMessages(entry.messages);
  };

  const deleteChat = (chatId, e) => {
    e.stopPropagation();
    setHistory(prev => {
      const updated = prev.filter(h => h.id !== chatId);
      try { localStorage.setItem('clinicon-chat-history', JSON.stringify(updated)); } catch {}
      return updated;
    });
    if (activeChat === chatId) {
      setActiveChat(null);
      setMessages([{ role: 'bot', text: t('chatWelcomeNew') }]);
    }
  };

  const clearAllChats = () => {
    setHistory([]);
    try { localStorage.removeItem('clinicon-chat-history'); } catch {}
    setActiveChat(null);
    setMessages([{ role: 'bot', text: t('chatWelcomeNew') }]);
  };

  const showSuggestions = messages.length <= 1 && !loading;

  return (
    <div className="chat-layout">
      {/* Chat History Sidebar */}
      <div className="chat-history-panel">
        <div className="chat-history-header">
          <span style={{ fontSize: 14.5, fontWeight: 700 }}>{t('chats')}</span>
          <div style={{ display: 'flex', gap: 4 }}>
            {history.length > 0 && (
              <button className="chat-new-btn" onClick={clearAllChats}
                title={t('deleteAll')}
                style={{ color: 'var(--danger)' }}>
                <Trash2 size={14} />
              </button>
            )}
            <button className="chat-new-btn" onClick={startNewChat} title={t('newChat')}>
              <Plus size={16} />
            </button>
          </div>
        </div>
        <div className="chat-history-list">
          {history.length === 0 ? (
            <div style={{ padding: '24px 16px', textAlign: 'center', color: 'var(--text-faint)', fontSize: 13 }}>
              {t('noChats')}
            </div>
          ) : (
            history.map(h => (
              <div key={h.id} className={`chat-history-item ${activeChat === h.id ? 'active' : ''}`}
                onClick={() => loadChat(h)} role="button" tabIndex={0}>
                <MessageSquare size={14} style={{ flexShrink: 0, color: 'var(--text-faint)' }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {h.title}
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 2 }}>{h.date}</div>
                </div>
                <button className="chat-delete-btn" onClick={(e) => deleteChat(h.id, e)}
                  title={t('delete')}>
                  <Trash2 size={13} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-container">
        <div className="chat-box">
          {/* Header */}
          <div className="chat-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <img src="/clinicon-icon.svg" alt="" className="chat-ai-logo" />
              <div>
                <div style={{ fontSize: 15, fontWeight: 700 }}>{t('aiAssistant')}</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: 12, color: 'var(--success)', marginTop: 3 }}>
                  {loading ? (
                    <span style={{ color: 'var(--warning)' }}>{t('thinking')}</span>
                  ) : (
                    <><span className="online-dot" style={{ width: 7, height: 7 }} /> {t('onlineNow')}</>
                  )}
                </div>
              </div>
            </div>
            <button onClick={startNewChat} className="btn-secondary"
              style={{ padding: '8px 14px', borderRadius: 'var(--radius-pill)', fontSize: 12.5 }}>
              <RotateCcw size={13} /> {t('newChat')}
            </button>
          </div>

          {/* Messages */}
          <div className="chat-messages" ref={scrollRef}>
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role === 'user' ? 'user' : ''}`}>
                {msg.role === 'user' ? (
                  <div className="chat-msg-avatar" style={{ background: 'var(--primary-light)', color: 'var(--primary)' }}>
                    {initial}
                  </div>
                ) : (
                  <img src="/clinicon-icon.svg" alt="" className="chat-ai-avatar" />
                )}
                <div className={`chat-bubble ${msg.role === 'user' ? 'user' : 'bot'}`}>
                  <BotText text={msg.text} />
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-msg">
                <img src="/clinicon-icon.svg" alt="" className="chat-ai-avatar" />
                <div className="chat-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}
          </div>

          {/* Suggestions */}
          {showSuggestions && (
            <div className="suggestion-chips">
              {getSuggestions(t).map(s => (
                <button key={s} className="suggestion-chip" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="chat-input-bar">
            <form onSubmit={e => { e.preventDefault(); send(); }}
              style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input value={input} onChange={e => setInput(e.target.value)} disabled={loading}
                placeholder={t('typeQuestion')}
                className="input-field" style={{ flex: 1, borderRadius: 12 }} />
              <button type="submit" disabled={loading || !input.trim()}
                className="btn-primary" style={{ padding: '14px 24px', borderRadius: 12, flexShrink: 0 }}>
                <Send size={16} />
              </button>
            </form>
            <div className="chat-disclaimer">
              {t('disclaimer')}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function getDisplayName(user) {
  const raw = user?.name || user?.full_name || '';
  if (!raw || raw.includes('@') || /^[a-zA-Z0-9._-]+$/.test(raw)) return '؟';
  return raw;
}

function BotText({ text }) {
  if (!text) return null;
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}
