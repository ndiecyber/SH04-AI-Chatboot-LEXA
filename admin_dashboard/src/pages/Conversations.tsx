import { useState, useEffect, useRef, ChangeEvent, KeyboardEvent } from 'react';
import { Search, User, Clock, MessageSquare, AlertCircle, Send, ShieldAlert, Bot, Headphones, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '../lib/apiClient';
import type { ChatSession, SessionHistory, Message, AdminReplyReq } from '../types/api';

interface SSEEvent {
  type: 'admin_reply' | 'handoff_user_msg' | 'done' | 'chunk' | 'typing' | 'error';
  content?: string;
  session_id?: string;
  message?: string;
  references?: Array<{ title: string; source: string; score: number }>;
}

interface HandoffNotification {
  session_id: string;
  user_name: string;
  timestamp: number;
}

const Conversations = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<SessionHistory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [handoffNotifications, setHandoffNotifications] = useState<HandoffNotification[]>([]);
  const [replyText, setReplyText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isUserTyping, setIsUserTyping] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch session list
  const fetchSessions = () => {
    api.authGet<{ items: ChatSession[]; total: number }>('/api/admin/sessions?limit=100')
      .then(data => {
        setSessions(data.items);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Error fetching sessions:", err);
        setIsLoading(false);
      });
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  // Admin WebSocket for handoff notifications
  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    
    const connectAdminWs = () => {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = window.location.host;
      const wsToken = localStorage.getItem('lexa_admin_token') || '';
      const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/admin?token=${wsToken}`);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'handoff_request' || data.type === 'new_message') {
            if (data.type === 'handoff_request') {
              setHandoffNotifications(prev => [...prev, {
                session_id: data.session_id,
                user_name: data.user_name,
                timestamp: data.timestamp,
              }]);
            }
            fetchSessions();
          }
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };

      ws.onclose = () => {
        reconnectTimeout = setTimeout(connectAdminWs, 3000);
      };
    };

    connectAdminWs();

    return () => {
      clearTimeout(reconnectTimeout);
    };
  }, []);

  // Fetch specific session history
  const loadSessionHistory = (sessionId: string) => {
    api.authGet<SessionHistory>(`/api/admin/sessions/${sessionId}`)
      .then(data => {
        setSessionData(data);
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      })
      .catch(err => console.error("Error fetching session history:", err));
  };

  // WebSocket connection for real-time sync
  useEffect(() => {
    if (!selectedSession) return;
    loadSessionHistory(selectedSession);
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/chat/${selectedSession}`);
    wsRef.current = ws;
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data) as SSEEvent;
            if (data.type === 'admin_reply' || data.type === 'handoff_user_msg' || data.type === 'done' || data.type === 'chunk') {
                if (data.type !== 'chunk') {
                    loadSessionHistory(selectedSession);
                }
                if (data.type === 'done') {
                    setIsUserTyping(false);
                }
            } else if (data.type === 'typing') {
                setIsUserTyping(true);
            }
        } catch(e) {}
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [selectedSession]);

  const handleToggleHandoff = () => {
    if (!sessionData) return;
    const newState = !sessionData.is_human_handoff;
    api.authPost(`/api/admin/handoff?session_id=${selectedSession}&is_handoff=${newState}`)
    .then(() => {
      setSessionData(prev => prev ? {...prev, is_human_handoff: newState} : null);
    })
    .catch(err => console.error("Error toggling handoff:", err));
  };

  const dismissNotification = (sessionId: string) => {
    setHandoffNotifications(prev => prev.filter(n => n.session_id !== sessionId));
  };

  const handleSendReply = () => {
    if (!replyText.trim() || !selectedSession) return;
    
    const payload: AdminReplyReq = { session_id: selectedSession, content: replyText };
    api.authPost('/api/admin/reply', payload)
    .then(() => {
      setReplyText('');
      loadSessionHistory(selectedSession);
    })
    .catch(err => console.error("Error sending reply:", err));
  };

  return (
    <div className="h-[calc(100vh-140px)] flex flex-col bg-white rounded-2xl shadow-[0_2px_10px_0_rgba(0,0,0,0.02)] border border-slate-100 overflow-hidden">
      
      {/* Handoff Notifications */}
      {handoffNotifications.map((notif) => (
        <div
          key={notif.session_id}
          className="bg-amber-50 border-b border-amber-200 px-4 py-3 flex items-center gap-3 animate-[slideDown_0.3s_ease-out]"
        >
          <Headphones className="w-5 h-5 text-amber-600 shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-amber-800">
              {notif.user_name} meminta obrolan dengan CS manusia
            </p>
            <p className="text-xs text-amber-600">
              Sesi: {notif.session_id.substring(0, 8)}...
            </p>
          </div>
          <button
            onClick={() => {
              setSelectedSession(notif.session_id);
              dismissNotification(notif.session_id);
            }}
            className="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-medium rounded-lg transition-colors"
          >
            Lihat
          </button>
          <button
            onClick={() => dismissNotification(notif.session_id)}
            className="p-1 text-amber-400 hover:text-amber-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}

      {/* Main Content */}
      <div className="w-1/3 border-r border-slate-100 flex flex-col bg-slate-50/50">
        <div className="p-4 border-b border-slate-100">
          <h2 className="font-bold text-slate-800 text-lg flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-600" /> 
            Active Conversations
          </h2>
          <div className="mt-4 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              placeholder="Cari ID Sesi atau pesan..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-slate-200 text-sm rounded-lg py-2 pl-9 pr-3 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto scrollbar-hidden p-2 space-y-1">
          {isLoading ? (
            <div className="p-4 text-center text-sm text-slate-500 animate-pulse">Loading sessions...</div>
          ) : sessions.length === 0 ? (
            <div className="p-4 text-center text-sm text-slate-500">Belum ada percakapan.</div>
          ) : (
            sessions
              .filter(s => {
                if (!searchQuery.trim()) return true;
                const q = searchQuery.toLowerCase();
                return s.session_id.toLowerCase().includes(q) ||
                       (s.last_message && s.last_message.toLowerCase().includes(q));
              })
              .map((s) => (
              <button 
                key={s.session_id}
                onClick={() => setSelectedSession(s.session_id)}
                className={`w-full text-left p-3 rounded-xl transition-colors ${selectedSession === s.session_id ? 'bg-blue-50 border border-blue-100 shadow-sm' : 'hover:bg-slate-100 border border-transparent'}`}
              >
                <div className="flex justify-between items-start mb-1">
                  <div className="font-semibold text-slate-800 text-sm truncate pr-2 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-400" />
                    {s.session_id.substring(0, 8)}...
                  </div>
                  <span className="text-[10px] text-slate-400 whitespace-nowrap flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(s.updated_at).toLocaleTimeString('id-ID', {hour: '2-digit', minute:'2-digit'})}
                  </span>
                </div>
                <p className="text-xs text-slate-500 truncate">{s.last_message || "Memulai percakapan..."}</p>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Right Pane: Chat History */}
      <div className="flex-1 flex flex-col bg-white">
        {selectedSession ? (
          <>
            <div className="p-4 border-b border-slate-100 flex justify-between items-center bg-white shadow-sm z-10">
              <div>
                <h3 className="font-bold text-slate-800">Sesi Pelanggan</h3>
                <p className="text-xs text-slate-500 font-mono mt-0.5">ID: {selectedSession}</p>
              </div>
              <button 
                onClick={handleToggleHandoff}
                className={`px-4 py-2 text-sm font-semibold rounded-xl border transition-colors flex items-center gap-2
                  ${sessionData?.is_human_handoff 
                    ? 'bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-200' 
                    : 'bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200'}`}
              >
                {sessionData?.is_human_handoff ? <ShieldAlert className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                {sessionData?.is_human_handoff ? 'Kembalikan ke AI' : 'Ambil Alih (Handoff)'}
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto scrollbar-hidden p-6 space-y-6 bg-slate-50/30">
              {!sessionData ? (
                <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
              ) : sessionData.history && sessionData.history.length > 0 ? (
                sessionData.history.map((msg: Message, idx) => {
                  const isUser = msg.role === 'user';
                  const isAdmin = msg.role === 'admin';
                  return (
                    <div key={idx} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
                      {!isUser && (
                        <span className="text-[10px] text-slate-400 mb-1 ml-1 font-medium uppercase tracking-wider">
                          {isAdmin ? 'Human Agent' : 'Lexa AI'}
                        </span>
                      )}
                      <div className={`max-w-[75%] rounded-2xl px-5 py-3.5 text-[14px] leading-relaxed shadow-sm ${
                        isUser 
                          ? 'bg-blue-600 text-white rounded-tr-sm' 
                          : isAdmin
                            ? 'bg-amber-500 text-white rounded-tl-sm markdown-body'
                            : 'bg-white text-slate-700 border border-slate-200/60 rounded-tl-sm markdown-body'
                      }`}>
                        {isUser ? msg.content : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {msg.content}
                            </ReactMarkdown>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-400">
                  <AlertCircle className="w-12 h-12 mb-3 text-slate-300" />
                  <p>Tidak ada pesan dalam sesi ini.</p>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            {/* Input Area (Only visible if Handoff is true) */}
            {sessionData?.is_human_handoff ? (
              <div className="p-4 border-t border-slate-100 bg-white">
                {isUserTyping && (
                  <div className="text-xs text-blue-500 mb-2 font-medium animate-pulse">
                    Pelanggan sedang mengetik...
                  </div>
                )}
                <div className="flex gap-2">
                  <textarea 
                    value={replyText}
                    onChange={(e: ChangeEvent<HTMLTextAreaElement>) => {
                      setReplyText(e.target.value);
                      if (wsRef.current?.readyState === WebSocket.OPEN) {
                        wsRef.current.send(JSON.stringify({ type: 'typing', role: 'admin' }));
                      }
                    }}
                    onKeyDown={(e: KeyboardEvent<HTMLTextAreaElement>) => {
                      if(e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendReply();
                      }
                    }}
                    placeholder="Ketik balasan untuk pelanggan..."
                    className="flex-1 resize-none border border-amber-200 bg-amber-50 rounded-xl px-4 py-2 outline-none focus:border-amber-400 text-sm"
                    rows={2}
                  />
                  <button 
                    onClick={handleSendReply}
                    className="px-4 bg-amber-500 hover:bg-amber-600 text-white rounded-xl flex items-center justify-center transition-colors"
                  >
                    <Send className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-[10px] text-amber-600 mt-2 font-medium">⚠️ Saat diambil alih, AI tidak akan otomatis membalas pesan pelanggan.</p>
              </div>
            ) : (
              <div className="p-4 border-t border-slate-100 bg-slate-50">
                <div className="flex items-center justify-center text-xs text-slate-500 bg-white p-3 rounded-xl border border-slate-200/60">
                  Klik tombol "Ambil Alih (Handoff)" di atas untuk membalas secara manual.
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <MessageSquare className="w-16 h-16 mb-4 text-slate-200" />
            <p className="text-lg font-medium text-slate-500">Pilih Percakapan</p>
            <p className="text-sm mt-1">Klik salah satu sesi di sebelah kiri untuk melihat riwayat chat.</p>
          </div>
        )}
      </div>

    </div>
  );
};

export default Conversations;