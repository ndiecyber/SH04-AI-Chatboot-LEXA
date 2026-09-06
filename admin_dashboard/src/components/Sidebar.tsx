import { LayoutDashboard, MessageSquare, BookOpen, BarChart3, Users, Settings, LogOut, ChevronsLeft, ChevronsRight } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import type { ReactNode } from 'react';

interface SidebarProps {
  setAuthToken: (token: string | null) => void;
  isCollapsed: boolean;
  onToggle: () => void;
}

interface NavItem {
  name: string;
  icon: ReactNode;
  path: string;
}

const Sidebar = ({ setAuthToken, isCollapsed, onToggle }: SidebarProps) => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('lexa_admin_token');
    localStorage.removeItem('lexa_admin_user');
    setAuthToken(null);
    navigate('/login');
  };

  const navItems: NavItem[] = [
    { name: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" />, path: '/' },
    { name: 'Conversations', icon: <MessageSquare className="w-5 h-5" />, path: '/conversations' },
    { name: 'Knowledge Base', icon: <BookOpen className="w-5 h-5" />, path: '/kb' },
    { name: 'Analytics', icon: <BarChart3 className="w-5 h-5" />, path: '/analytics' },
    { name: 'Users & Roles', icon: <Users className="w-5 h-5" />, path: '/users' },
    { name: 'Settings', icon: <Settings className="w-5 h-5" />, path: '/settings' },
  ];

  return (
    <aside className={`${isCollapsed ? 'w-[72px]' : 'w-64'} bg-slate-900 dark:bg-slate-950 text-white flex flex-col h-screen fixed left-0 top-0 shadow-2xl transition-all duration-300 z-50`}>
      {/* Logo + Toggle */}
      <div className={`p-4 flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
        {!isCollapsed && (
          <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="bg-white p-1.5 rounded-xl flex items-center justify-center shadow-lg">
              <img src="/lexa_chatbot_logo.png" alt="Lexa Logo" className="w-8 h-8 object-contain" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">LEXA</h1>
              <p className="text-[10px] text-blue-300 font-medium tracking-widest uppercase">AI Platform</p>
            </div>
          </Link>
        )}
        {isCollapsed && (
          <div className="bg-white p-1.5 rounded-xl flex items-center justify-center shadow-lg">
            <img src="/lexa_chatbot_logo.png" alt="Lexa Logo" className="w-8 h-8 object-contain" />
          </div>
        )}
        <button
          onClick={onToggle}
          className={`p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors ${isCollapsed ? 'mt-2' : ''}`}
        >
          {isCollapsed ? <ChevronsRight className="w-4 h-4" /> : <ChevronsLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto scrollbar-hidden mt-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.name}
              to={item.path}
              title={isCollapsed ? item.name : undefined}
              className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 ${
                isCollapsed ? 'justify-center' : ''
              } ${
                isActive
                  ? 'bg-blue-600 text-white font-medium shadow-lg shadow-blue-600/20'
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className={`w-5 h-5 shrink-0 ${isActive ? 'text-white' : 'text-slate-400'}`}>{item.icon}</span>
              {!isCollapsed && <span className="text-sm">{item.name}</span>}
            </Link>
          );
        })}
        <button
          onClick={handleLogout}
          title={isCollapsed ? 'Logout' : undefined}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 text-red-400 hover:bg-red-500/10 hover:text-red-400 mt-4 ${isCollapsed ? 'justify-center' : ''}`}
        >
          <LogOut className="w-5 h-5 shrink-0" />
          {!isCollapsed && <span className="text-sm">Logout</span>}
        </button>
      </nav>

      {/* Bottom Card */}
      {!isCollapsed && (
        <div className="p-4 mt-auto">
          <div className="bg-white/5 rounded-2xl p-4 relative overflow-hidden group border border-white/10 shadow-lg">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/30 to-purple-600/30 opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="relative z-10 flex flex-col items-center text-center gap-2">
              <div className="w-14 h-14 rounded-full flex items-center justify-center">
                <img src="/lexa_bot.png" alt="Lexa Bot" className="w-full h-full object-contain drop-shadow-xl" />
              </div>
              <h3 className="font-semibold text-sm">LEXA CS Bot</h3>
              <p className="text-[11px] text-slate-300/80 leading-tight">Smarter Answers, Better Experiences</p>
              <a
                href="https://github.com/anomalyco/opencode"
                target="_blank"
                rel="noreferrer"
                className="mt-2 w-full py-2 bg-white/10 hover:bg-white/20 text-xs font-medium rounded-lg transition-colors border border-white/10 block text-center"
              >
                Documentation
              </a>
            </div>
          </div>
          <p className="text-[10px] text-slate-500 text-center mt-4">
            © 2026 LEXA Technology<br/>All rights reserved.
          </p>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;