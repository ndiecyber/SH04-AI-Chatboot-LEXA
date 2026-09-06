import { useState, useEffect } from 'react';
import { MessageSquare, Users, AlertCircle, Activity, Plus, FileText } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../lib/apiClient';
import type { KPIStats, ChartDataPoint, UnansweredQuery } from '../types/api';

const Dashboard = () => {
  const [stats, setStats] = useState<KPIStats>({
    active_users: 0,
    total_conversations: 0,
    unanswered_queries: 0
  });
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [unansweredList, setUnansweredList] = useState<UnansweredQuery[]>([]);
  
  useEffect(() => {
    api.authGet<{ kpi: KPIStats; chart: ChartDataPoint[] }>('/api/admin/stats')
      .then(data => {
        if(data.kpi) {
          setStats(data.kpi);
          setChartData(data.chart);
        }
      })
      .catch(err => console.error("Error fetching stats:", err));
      
    api.authGet<UnansweredQuery[]>('/api/admin/unanswered')
      .then(data => {
        if (Array.isArray(data)) setUnansweredList(data);
      })
      .catch(err => console.error("Error fetching unanswered queries:", err));
  }, []);

  const kpiData: Array<{
    title: string;
    value: string | number;
    trend: string;
    trendUp: boolean;
    icon: React.ComponentType<{ className?: string }>;
    color: string;
    bg: string;
  }> = [
    { title: 'Total Conversations', value: stats.total_conversations.toLocaleString(), trend: 'Real-time', trendUp: true, icon: MessageSquare, color: 'text-purple-600', bg: 'bg-purple-100' },
    { title: 'Unanswered Queries', value: stats.unanswered_queries.toLocaleString(), trend: 'Real-time', trendUp: false, icon: AlertCircle, color: 'text-red-600', bg: 'bg-red-100' },
    { title: 'Active Users (30m)', value: stats.active_users.toLocaleString(), trend: 'Real-time', trendUp: true, icon: Users, color: 'text-green-600', bg: 'bg-green-100' },
    { title: 'Resolution Rate', value: stats.total_conversations > 0 ? `${((1 - stats.unanswered_queries / Math.max(stats.total_conversations, 1)) * 100).toFixed(1)}%` : '—', trend: 'vs total', trendUp: true, icon: Activity, color: 'text-blue-600', bg: 'bg-blue-100' },
  ];
  
  return (
    <div className="space-y-6 pb-12">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 text-white shadow-xl shadow-blue-900/20">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        <div className="absolute bottom-0 right-1/4 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl translate-y-1/2"></div>
        
        <div className="relative z-10 p-8 md:p-10 flex flex-col md:flex-row justify-between items-center">
          <div className="max-w-2xl space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-sm font-medium">
              Welcome back, Admin LEXA! 👋
            </div>
            <h1 className="text-3xl md:text-4xl font-bold leading-tight">
              Monitor. Analyze. Improve. <br/>
              <span className="text-blue-300">Intelligent CS Assistant</span>
            </h1>
            <p className="text-blue-100/80 text-sm md:text-base">
              Pantau performa chatbot CS Anda, analisis pertanyaan yang belum terjawab, dan perbarui basis pengetahuan secara instan.
            </p>
            <div className="flex gap-4 pt-2">
              <button
                onClick={() => window.location.href = '/kb'}
                className="px-5 py-2.5 bg-blue-500 hover:bg-blue-400 text-white font-medium rounded-xl transition-colors shadow-lg shadow-blue-500/30 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" /> Sync Knowledge Base
              </button>
              <button
                onClick={() => window.location.href = '/analytics'}
                className="px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl transition-colors border border-white/20 flex items-center gap-2"
              >
                <FileText className="w-4 h-4" /> Lihat Laporan
              </button>
            </div>
          </div>
          
          <div className="hidden lg:block relative z-20">
            <div className="relative w-56 h-56 flex items-center justify-center">
              <div className="absolute inset-0 bg-blue-500/20 rounded-full animate-ping"></div>
              <div className="absolute inset-4 bg-gradient-to-tr from-blue-600/30 to-indigo-400/30 rounded-full rotate-12 opacity-80 blur-lg"></div>
              <img src="/lexa_bot.png" alt="Lexa Hero" className="relative z-10 w-full h-full object-contain drop-shadow-[0_0_30px_rgba(59,130,246,0.6)] hover:scale-105 transition-transform duration-500" />
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiData.map((kpi, idx) => (
          <div key={idx} className="bg-white rounded-2xl p-6 shadow-[0_2px_10px_0_rgba(0,0,0,0.02)] border border-slate-100 card-hover">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">{kpi.title}</p>
                <h3 className="text-2xl font-bold text-slate-800 mt-2">{kpi.value}</h3>
              </div>
              <div className={`p-3 rounded-xl ${kpi.bg}`}>
                <kpi.icon className={`w-6 h-6 ${kpi.color}`} />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <span className={kpi.trendUp ? 'text-green-500 font-medium' : 'text-red-500 font-medium'}>
                {kpi.trend}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chart Section */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 shadow-[0_2px_10px_0_rgba(0,0,0,0.02)] border border-slate-100">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-bold text-slate-800 text-lg">Statistik Percakapan</h3>
            <span className="text-xs text-slate-400 font-medium">7 Hari Terakhir</span>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dx={-10} />
                <Tooltip 
                  contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,0.1)' }}
                  cursor={{ stroke: '#cbd5e1', strokeWidth: 1, strokeDasharray: '4 4' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="percakapan" 
                  stroke="#3b82f6" 
                  strokeWidth={3}
                  dot={{ r: 4, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }}
                  activeDot={{ r: 6, fill: '#2563eb', strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-2xl p-6 shadow-[0_2px_10px_0_rgba(0,0,0,0.02)] border border-slate-100 flex flex-col">
          <h3 className="font-bold text-slate-800 text-lg mb-6">Unanswered Queries</h3>
          <div className="space-y-6 flex-1">
            {unansweredList.length === 0 ? (
              <p className="text-slate-500 text-sm italic">Belum ada pertanyaan yang gagal dijawab hari ini.</p>
            ) : unansweredList.map((item, idx) => (
              <div key={idx} className="flex gap-4">
                <div className="relative mt-1">
                  <div className="w-2.5 h-2.5 rounded-full z-10 relative bg-red-500 ring-4 ring-red-100"></div>
                  {idx !== unansweredList.length - 1 && (
                    <div className="absolute top-3 left-1/2 -translate-x-1/2 w-[2px] h-12 bg-slate-100"></div>
                  )}
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-800 leading-snug">"{item.query}"</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-slate-400">{new Date(item.created_at).toLocaleString('id-ID')}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <button className="w-full mt-4 py-2.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-xl transition-colors">
            Lihat Semua Aktivitas →
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;