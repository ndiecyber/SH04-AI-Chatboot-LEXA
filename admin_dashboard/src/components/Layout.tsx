import { useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  setAuthToken: (token: string | null) => void;
}

const Layout = ({ setAuthToken }: LayoutProps) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return localStorage.getItem('lexa_sidebar_collapsed') === 'true';
  });

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => {
      const next = !prev;
      localStorage.setItem('lexa_sidebar_collapsed', String(next));
      return next;
    });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors">
      <Sidebar
        setAuthToken={setAuthToken}
        isCollapsed={sidebarCollapsed}
        onToggle={toggleSidebar}
      />
      <div className={`${sidebarCollapsed ? 'ml-[72px]' : 'ml-64'} transition-all duration-300`}>
        <Header onToggleSidebar={toggleSidebar} sidebarCollapsed={sidebarCollapsed} />
        <main className="p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;