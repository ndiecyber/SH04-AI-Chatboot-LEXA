import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Minus, RotateCcw, GripHorizontal, Headphones } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import lexaBotHead from './assets/lexa_bot_transparent.png';
import api from './lib/apiClient';
import type { Message, WidgetConfig, SSEEvent } from './types/api';

interface ChatMessage extends Message {
  id: number;
}

type ExtendedSSEEvent = SSEEvent | 
  { type: 'admin_reply'; content: string } | 
  { type: 'handoff_user_msg'; content: string } |
  { type: 'handoff_requested' } |
  { type: 'typing' };

function App() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [isAdminTyping, setIsAdminTyping] = useState(false);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('lexa_session_id') || '');
  const [config, setConfig] = useState<WidgetConfig | null>(null);
  const [escalationShown, setEscalationShown] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isHandoffRequested, setIsHandoffRequested] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // Initialize & fetch config
  useEffect(() => {
    let savedMessages: ChatMessage[] = [];
    try {
      savedMessages = JSON.parse(localStorage.getItem('lexa_messages') || '[]') as ChatMessage[];
    } catch {
      savedMessages = [];
    }
    setMessages(savedMessages);

    api.get<WidgetConfig>('/config')
      .then((data: WidgetConfig) => {
        setConfig(data);
        if (savedMessages.length === 0) {
          const welcomeMsg: ChatMessage = {
            id: Date.now(),
            role: 'bot',
            content: data.welcome_message,
            timestamp: Date.now()
          };
          setMessages([welcomeMsg]);
          localStorage.setItem('lexa_messages', JSON.stringify([welcomeMsg]));
        }
      })
      .catch(err => console.error("Failed to load config", err));
  }, []);

  // Save session & messages
  useEffect(() => {
    localStorage.setItem('lexa_session_id', sessionId);
    if (messages.length > 0) {
      localStorage.setItem('lexa_messages', JSON.stringify(messages));
    }
  }, [messages, sessionId]);


  // WebSocket connection for real-time sync (replaces polling)
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>(null);

  const connectWebSocket = useCallback(() => {
    if (!sessionId) return;
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host;
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/chat/${sessionId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ExtendedSSEEvent;
        if (data.type === 'admin_reply' || data.type === 'handoff_user_msg') {
          api.get<{ history: Array<{ role: string; content: string; timestamp?: number }> }>(`/api/chat/poll?session_id=${sessionId}&t=${Date.now()}`)
            .then((pollData) => {
              if (pollData.history && pollData.history.length > 0) {
                const mappedHistory = pollData.history.map((m, i) => ({
                  id: m.timestamp || Date.now() + i,
                  role: m.role === 'assistant' ? 'bot' : m.role,
                  content: m.content,
                  timestamp: m.timestamp || Date.now()
                })) as ChatMessage[];
                setMessages(prev => {
                  const welcomeMsg = prev.length > 0 && prev[0].role === 'bot' ? prev[0] : null;
                  const newMsgs = welcomeMsg ? [welcomeMsg, ...mappedHistory] : mappedHistory;
                  const strip = (msgs: ChatMessage[]) => JSON.stringify(msgs.map(m => ({role: m.role, content: m.content})));
                  return strip(prev) !== strip(newMsgs) ? newMsgs : prev;
                });
              }
            })
            .catch(() => {});
        } else if (data.type === 'handoff_requested') {
          setIsHandoffRequested(true);
        } else if (data.type === 'typing') {
          if (data.role === 'admin') {
            setIsAdminTyping(true);
          } else {
            setIsWaitingForResponse(true);
          }
        } else if (data.type === 'done') {
          api.get<{ history: Array<{ role: string; content: string; timestamp?: number }> }>(`/api/chat/poll?session_id=${sessionId}&t=${Date.now()}`)
            .then((pollData) => {
              if (pollData.history && pollData.history.length > 0) {
                const mappedHistory = pollData.history.map((m, i) => ({
                  id: m.timestamp || Date.now() + i,
                  role: m.role === 'assistant' ? 'bot' : m.role,
                  content: m.content,
                  timestamp: m.timestamp || Date.now()
                })) as ChatMessage[];
                setMessages(prev => {
                  const welcomeMsg = prev.length > 0 && prev[0].role === 'bot' ? prev[0] : null;
                  const newMsgs = welcomeMsg ? [welcomeMsg, ...mappedHistory] : mappedHistory;
                  const strip = (msgs: ChatMessage[]) => JSON.stringify(msgs.map(m => ({role: m.role, content: m.content})));
                  return strip(prev) !== strip(newMsgs) ? newMsgs : prev;
                });
              }
            })
            .catch(() => {});
          setIsWaitingForResponse(false);
        }
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    };

    ws.onclose = () => {
      reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {};
  }, [sessionId]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connectWebSocket]);

  // Auto scroll
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isStreaming, isWaitingForResponse]);

  const handleSend = async (textToSend = input) => {
    const text = textToSend.trim();
    if (!text || isStreaming || isWaitingForResponse) return;

    setInput('');
    const userMsg: ChatMessage = { id: Date.now(), role: 'user', content: text, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setIsWaitingForResponse(true);

    try {
      const response = await api.stream('/chat/stream', { message: text, session_id: sessionId });

      if (!response.ok) throw new Error('API Error');

const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullResponse = '';
      let botMsgId: number = 0;
      let isFirstChunk = true;

      if (!reader) throw new Error('No response body');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6);

          try {
            const data = JSON.parse(jsonStr) as ExtendedSSEEvent;
            if (data.type === 'session') {
              setSessionId(data.session_id);
            } else if (data.type === 'chunk') {
              if (isFirstChunk) {
                 isFirstChunk = false;
                 setIsWaitingForResponse(false);
                 botMsgId = Date.now() + 1;
                 setMessages(prev => [...prev, { id: botMsgId, role: 'bot', content: '', timestamp: Date.now() }]);
              }
              
              fullResponse += data.content;
              setMessages(prev => 
                prev.map(m => m.id === botMsgId ? { ...m, content: fullResponse } : m)
              );
            } else if (data.type === 'error') {
               throw new Error(data.message);
            }
          } catch (e) {
            // ignore parse errors
          }
        }
      }
      
      const userMessageCount = messages.filter(m => m.role === 'user').length + 1;
      if (userMessageCount >= 5 && !escalationShown) {
        setEscalationShown(true);
      }

    } catch (error) {
       setIsWaitingForResponse(false);
       setMessages(prev => [...prev, { 
         id: Date.now(), 
         role: 'bot', 
         content: 'Maaf, terjadi kesalahan. Silakan coba lagi.', 
         timestamp: Date.now() 
       }]);
    } finally {
      setIsStreaming(false);
      setIsWaitingForResponse(false);
    }
  };

  const handleReset = async () => {
    setIsRefreshing(true);
    if (sessionId) {
      try {
        await api.post(`/chat/reset?session_id=${sessionId}`);
      } catch (e) {
        console.error('WebSocket message parse error:', e);
      }
    }
    
    setSessionId('');
    setEscalationShown(false);
    
    setTimeout(() => {
        if (config) {
          const welcomeMsg: ChatMessage = { id: Date.now(), role: 'bot', content: config.welcome_message, timestamp: Date.now() };
          setMessages([welcomeMsg]);
          localStorage.setItem('lexa_messages', JSON.stringify([welcomeMsg]));
        } else {
          setMessages([]);
          localStorage.removeItem('lexa_messages');
        }
        setIsRefreshing(false);
    }, 600); // efek jeda animasi
  };

  const handleRequestHandoff = () => {
    if (!sessionId || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type: 'handoff_request', user_name: 'Customer' }));
    setIsHandoffRequested(true);
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'bot',
      content: 'Permintaan obrolan dengan CS manusia sudah dikirim. Mohon tunggu sebentar...',
      timestamp: Date.now()
    }]);
  };

  const showQuickReplies = config?.quick_replies && messages.length <= 2 && !isStreaming && !isWaitingForResponse && window.innerWidth > 480;

  return (
    <div className="fixed inset-0 pointer-events-none z-[99999] font-sans">
      
      {/* Floating Button (Bouncy entry) */}
      <motion.div 
        className="absolute bottom-6 right-6 pointer-events-auto"
        initial={{ scale: 0, y: 50 }}
        animate={{ scale: isOpen ? 0 : 1, y: isOpen ? 50 : 0 }}
        transition={{ type: "spring", stiffness: 260, damping: 20 }}
      >
        <button 
          onClick={() => setIsOpen(true)}
          className="w-[64px] h-[64px] bg-transparent text-white flex items-center justify-center  transition-colors"
        >
          {/* Menggunakan image kepala robot yang transparan */}
          <img src={lexaBotHead} alt="Lexa" className="w-[48px] h-[48px] object-contain drop-shadow-md" />
        </button>
      </motion.div>

      {/* Chat Panel - Draggable with Framer Motion */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            ref={panelRef}
            drag
            dragConstraints={{ left: -800, right: 0, top: -800, bottom: 0 }}
            dragElastic={0.1}
            dragMomentum={false}
            initial={{ opacity: 0, y: 50, scale: 0.9, originX: 1, originY: 1 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 30, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 350, damping: 25 }}
            style={{ position: 'absolute', bottom: '24px', right: '24px' }}
            className="w-[380px] h-[640px] min-w-[320px] min-h-[400px] max-w-[90vw] max-h-[calc(100vh-100px)] resize overflow-hidden bg-white/95 backdrop-blur-xl rounded-[24px] shadow-[0_20px_60px_-15px_rgba(0,0,0,0.3)] border border-slate-200/50 flex flex-col pointer-events-auto"
          >
            {/* Header (Drag Handle) */}
            <div className="cursor-grab active:cursor-grabbing flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-white/80 shrink-0 z-10 relative">
              <div className="absolute top-1.5 left-1/2 -translate-x-1/2 text-slate-300">
                 <GripHorizontal size={24} />
              </div>
              <div className="flex items-center gap-3 mt-1 pointer-events-none">
                 <div className="relative">
                    {/* Hapus background frame agar murni kepalanya saja */}
                    <img src={lexaBotHead} alt="Lexa Avatar" className="w-11 h-11 object-contain drop-shadow-sm" />
                    <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                 </div>
                 <div>
                    <h2 className="text-[15px] font-bold text-slate-800 leading-tight">Lexa Chat Widget V5</h2>
                    <p className="text-xs text-green-500 font-medium mt-0.5">Online</p>
                 </div>
              </div>
              <div className="flex gap-1 mt-1 z-20">
                 <button onClick={handleReset} className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors" title="Refresh/Reset">
                   <RotateCcw size={18} className={isRefreshing ? "animate-spin text-blue-600" : ""} />
                 </button>
                 <button onClick={() => setIsOpen(false)} className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors" title="Tutup">
                   <Minus size={18} />
                 </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto scrollbar-hidden p-5 space-y-6 bg-slate-50/50 scroll-smooth relative">
              <AnimatePresence>
                {messages.map((msg, idx) => {
                  const isUser = msg.role === 'user';
                  const isAdmin = msg.role === 'admin';
                  return (
                    <motion.div 
                      key={msg.id || idx} 
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`flex gap-3 max-w-[90%] ${isUser ? 'ml-auto flex-row-reverse' : ''}`}
                    >
                       {!isUser && (
                          <div className="w-9 h-9 flex-shrink-0 flex items-start justify-center mt-0.5">
                             <img src={lexaBotHead} alt="bot" className="w-full h-full object-contain drop-shadow-sm" />
                          </div>
                       )}
                       <div className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
                          <div className={`px-4 py-3 text-[14px] leading-[1.6] shadow-sm break-words whitespace-pre-wrap ${
                              isUser 
                                ? 'bg-blue-600 text-white rounded-2xl rounded-tr-sm' 
                                : isAdmin
                                  ? 'bg-amber-100 text-amber-900 border border-amber-200 rounded-2xl rounded-tl-sm markdown-body'
                                  : 'bg-white text-slate-700 border border-slate-200/60 rounded-2xl rounded-tl-sm markdown-body'
                            }`}>
                           {isUser ? msg.content : (
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                               {msg.content}
                             </ReactMarkdown>
                           )}
                          </div>
                          <span className="text-[10px] text-slate-400 px-1 font-medium mt-0.5">
                            {new Intl.DateTimeFormat('id-ID', { hour: '2-digit', minute: '2-digit' }).format(msg.timestamp)}
                          </span>
                       </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>

              {/* Typing Indicator with Framer Motion Bounce */}
              <AnimatePresence>
                {(isWaitingForResponse || isAdminTyping) && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="flex gap-3 max-w-[90%]"
                  >
                     <div className="w-10 h-10 flex-shrink-0 flex items-start justify-center mt-0.5">
                        <motion.img 
                          src={lexaBotHead} 
                          alt="typing" 
                          className="w-full h-full object-contain drop-shadow-sm" 
                          animate={{ y: [0, -8, 0] }}
                          transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                        />
                     </div>
                     <div className="flex flex-col items-start gap-1">
                         {isAdminTyping && (
                           <span className="text-[10px] text-amber-500 font-medium">CS Agent sedang mengetik...</span>
                         )}
                         <div className="bg-white border border-slate-200/60 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm h-11 flex items-center justify-center">
                             <div className="flex gap-1.5 items-center">
                                 <motion.div animate={{y:[0,-4,0]}} transition={{repeat:Infinity, duration:0.6, delay:0}} className="w-1.5 h-1.5 bg-blue-400 rounded-full"></motion.div>
                                 <motion.div animate={{y:[0,-4,0]}} transition={{repeat:Infinity, duration:0.6, delay:0.2}} className="w-1.5 h-1.5 bg-blue-400 rounded-full"></motion.div>
                                 <motion.div animate={{y:[0,-4,0]}} transition={{repeat:Infinity, duration:0.6, delay:0.4}} className="w-1.5 h-1.5 bg-blue-400 rounded-full"></motion.div>
                             </div>
                         </div>
                     </div>
                  </motion.div>
                )}
              </AnimatePresence>

              <div ref={messagesEndRef} />
            </div>

            {/* Quick Replies */}
            {showQuickReplies && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="px-5 pb-4 pt-1 flex flex-wrap gap-2 bg-slate-50/50 shrink-0"
              >
                {config.quick_replies.map((text, i) => (
                  <button 
                    key={i} 
                    onClick={() => handleSend(text)}
                    className="px-4 py-2 bg-white/80 backdrop-blur-sm border border-blue-200 text-blue-600 hover:bg-blue-600 hover:text-white text-[13px] font-medium rounded-full shadow-sm transition-all active:scale-95 text-left"
                  >
                    {text}
                  </button>
                ))}
              </motion.div>
            )}

            {/* Escalation */}
            <AnimatePresence>
              {isHandoffRequested ? (
                 <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="px-5 py-3 bg-blue-50/90 backdrop-blur-md border-t border-blue-200 flex items-center gap-3 shrink-0"
                  >
                    <Headphones className="w-5 h-5 text-blue-600 shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs font-semibold text-blue-800">Menunggu CS Manusia</p>
                      <p className="text-[10px] text-blue-600">Tim kami akan segera merespon.</p>
                    </div>
                  </motion.div>
              ) : escalationShown && (
                 <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="px-5 py-3 bg-amber-50/90 backdrop-blur-md border-t border-amber-200 flex items-center justify-between shrink-0"
                  >
                    <span className="text-xs font-semibold text-amber-800">Butuh bantuan manusia?</span>
                    <button 
                       onClick={handleRequestHandoff}
                       className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white text-[11px] font-bold uppercase tracking-wider rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
                    >
                       <Headphones className="w-3.5 h-3.5" />
                       Chat CS
                    </button>
                  </motion.div>
              )}
            </AnimatePresence>

            {/* Input Area */}
            <div className="p-4 bg-white/90 backdrop-blur-xl border-t border-slate-200/60 shrink-0 z-10 relative">
              <div className="flex items-end gap-3">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder="Ketik pertanyaan Anda..."
                  className="flex-1 max-h-[120px] min-h-[48px] bg-slate-100/70 border border-transparent focus:border-blue-500 focus:ring-2 focus:ring-blue-100 focus:bg-white rounded-[24px] px-5 py-3.5 text-[14px] text-slate-700 outline-none resize-none transition-all"
                  rows={1}
                />
                <button
                  onClick={() => handleSend()}
                  disabled={!input.trim() || isStreaming || isWaitingForResponse}
                  className="w-[48px] h-[48px] shrink-0 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-full flex items-center justify-center shadow-md shadow-blue-500/20 transition-all active:scale-95"
                >
                  <Send size={18} className="ml-1" />
                </button>
              </div>
              <div className="text-center mt-3 mb-1">
                 <span className="text-[9px] text-slate-400 font-bold tracking-widest uppercase" style={{ fontSize: window.innerWidth < 480 ? '8px' : '9px' }}>Powered by LEXA Software House</span>
              </div>
            </div>

          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;