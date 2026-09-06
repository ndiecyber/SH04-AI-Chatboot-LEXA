import { useState, useEffect, useCallback, useRef } from 'react';
import { Search, Bell, HelpCircle, Menu, X, Sun, Moon } from 'lucide-react';

interface Notification {
  id: string;
  message: string;
  session_id?: string;
  timestamp: Date;
  read: boolean;
}

interface HeaderProps {
  onToggleSidebar?: () => void;
  sidebarCollapsed?: boolean;
}

const Header = ({ onToggleSidebar }: HeaderProps) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [isDark, setIsDark] = useState(() => localStorage.getItem('lexa_dark_mode') === 'true');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const unreadCount = notifications.filter(n => !n.read).length;

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('lexa_dark_mode', String(isDark));
  }, [isDark]);

  useEffect(() => {
    const token = localStorage.getItem('lexa_admin_token');
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/admin${token ? `?token=${token}` : ''}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'handoff_request') {
          setNotifications(prev => [{
            id: crypto.randomUUID(),
            message: `User ${data.user_id || 'Anonymous'} meminta bantuan CS manusia`,
            session_id: data.session_id,
            timestamp: new Date(),
            read: false,
          }, ...prev]);
        }
      } catch {}
    };

    return () => ws.close();
  }, []);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const markAllRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  return (
    <header className="h-20 bg-white/50 dark:bg-slate-800/50 backdrop-blur-md border-b border-slate-200/50 dark:border-slate-700/50 flex items-center justify-between px-8 sticky top-0 z-40 transition-colors">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
        >
          <Menu className="w-6 h-6" />
        </button>
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200 hidden md:block">Dashboard</h2>
      </div>

      <div className="flex-1 max-w-xl px-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
          <input
            type="text"
            placeholder="Search anything..."
            className="w-full bg-slate-100/50 dark:bg-slate-700/50 border border-slate-200 dark:border-slate-600 text-sm rounded-full py-2.5 pl-10 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1">
            <span className="text-[10px] font-medium text-slate-400 border border-slate-200 rounded px-1.5 py-0.5">⌘K</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-5">
        {/* Dark Mode Toggle */}
        <button
          onClick={() => setIsDark(!isDark)}
          className="text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
          title={isDark ? 'Light Mode' : 'Dark Mode'}
        >
          {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* Notification Bell */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 relative"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1">
                {unreadCount}
              </span>
            )}
          </button>

          {showDropdown && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-white dark:bg-slate-800 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden z-50 animate-in slide-in-from-top-2">
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-700">
                <h3 className="font-semibold text-sm text-slate-800 dark:text-slate-200">Notifikasi</h3>
                <div className="flex gap-2">
                  {unreadCount > 0 && (
                    <button onClick={markAllRead} className="text-[11px] text-blue-600 hover:text-blue-700 font-medium">
                      Tandai semua dibaca
                    </button>
                  )}
                  {notifications.length > 0 && (
                    <button onClick={clearAll} className="text-[11px] text-slate-400 hover:text-slate-600">
                      Hapus semua
                    </button>
                  )}
                </div>
              </div>

              <div className="max-h-64 overflow-y-auto scrollbar-hidden">
                {notifications.length === 0 ? (
                  <div className="py-8 text-center text-slate-400 dark:text-slate-500 text-sm">
                    Tidak ada notifikasi
                  </div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`px-4 py-3 border-b border-slate-50 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors ${
                        !n.read ? 'bg-blue-50/50 dark:bg-blue-900/20' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        {!n.read && (
                          <span className="mt-1.5 w-2 h-2 bg-blue-500 rounded-full shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-slate-700 dark:text-slate-300 leading-snug">{n.message}</p>
                          <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
                            {n.timestamp.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                        <button
                          onClick={() => setNotifications(prev => prev.filter(x => x.id !== n.id))}
                          className="text-slate-300 dark:text-slate-600 hover:text-slate-500 dark:hover:text-slate-400 shrink-0"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <button className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300">
          <HelpCircle className="w-5 h-5" />
        </button>
        <div className="h-8 w-[1px] bg-slate-200 dark:bg-slate-700"></div>
        <div className="flex items-center gap-3 cursor-pointer group">
          <div className="w-9 h-9 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium group-hover:ring-4 ring-blue-500/20 transition-all">
            A
          </div>
          <div className="hidden md:block text-right">
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-tight">Admin LEXA</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">Super Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;