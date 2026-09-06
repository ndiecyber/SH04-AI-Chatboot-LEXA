import { useState, useEffect, FormEvent, ChangeEvent } from 'react';
import { Shield, ShieldAlert, User, Plus, Trash2, X, MessageSquare } from 'lucide-react';
import api from '../lib/apiClient';
import type { AdminUser, UserCreateRequest } from '../types/api';

const Users = () => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState<UserCreateRequest>({
    name: '',
    email: '',
    password: '',
    role: 'CS Agent'
  });

  const fetchUsers = () => {
    api.authGet<{ items: AdminUser[]; total: number }>('/api/admin/users?limit=100')
      .then(data => setUsers(data.items))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleDelete = (id: number) => {
    if (window.confirm('Hapus pengguna ini?')) {
      api.authDelete(`/api/admin/users/${id}`)
        .then(() => {
          fetchUsers();
        })
        .catch(err => {
          console.error(err);
          alert(err.message || 'Gagal menghapus pengguna.');
        });
    }
  };

  const handleAdd = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    api.authPost('/api/admin/users', formData)
    .then(() => {
      setIsModalOpen(false);
      setFormData({ name: '', email: '', password: '', role: 'CS Agent' });
      fetchUsers();
    })
    .catch(err => {
      console.error(err);
      alert(err.message || 'Gagal menambah pengguna.');
    });
  };

  return (
    <div className="p-6 max-w-6xl relative">
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Users & Roles</h1>
          <p className="text-slate-500">Kelola akses tim ke Dashboard Lexa.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-sm"
        >
          <Plus className="w-4 h-4" />
          Tambah Anggota
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 text-sm">
                <th className="px-6 py-4 font-medium">Nama Anggota</th>
                <th className="px-6 py-4 font-medium">Role</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Terakhir Aktif</th>
                <th className="px-6 py-4 font-medium text-right">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold
                        ${user.role === 'Super Admin' ? 'bg-indigo-500' : 
                          user.role === 'Editor (Knowledge Base)' ? 'bg-orange-500' : 'bg-blue-500'}`}
                      >
                        {user.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-slate-800">{user.name}</p>
                        <p className="text-xs text-slate-500">{user.email}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2 text-sm text-slate-700">
                      {user.role === 'Super Admin' && <ShieldAlert className="w-4 h-4 text-indigo-500" />}
                      {user.role === 'CS Agent' && <User className="w-4 h-4 text-blue-500" />}
                      {user.role === 'Editor (Knowledge Base)' && <Shield className="w-4 h-4 text-orange-500" />}
                      {user.role}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium
                      ${user.status === 'Online' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${user.status === 'Online' ? 'bg-green-500' : 'bg-slate-400'}`}></span>
                      {user.status || 'Offline'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500">
                    {user.last_active || 'Baru Saja'}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => handleDelete(user.id)} className="text-red-400 hover:text-red-600 p-2 rounded-md hover:bg-red-50 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-slate-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p>Belum ada anggota tim terdaftar.</p>
                    <p className="text-xs text-slate-400 mt-1">Klik "Tambah Anggota" untuk memulai.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6 border-b border-slate-100 flex justify-between items-center">
              <h2 className="text-lg font-bold text-slate-800">Tambah Anggota Tim</h2>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAdd} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nama Lengkap</label>
                <input required type="text" value={formData.name} onChange={(e: ChangeEvent<HTMLInputElement>) => setFormData({...formData, name: e.target.value})} className="w-full border border-slate-200 rounded-lg px-4 py-2 outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
                <input required type="email" value={formData.email} onChange={(e: ChangeEvent<HTMLInputElement>) => setFormData({...formData, email: e.target.value})} className="w-full border border-slate-200 rounded-lg px-4 py-2 outline-none focus:border-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
                <input required type="password" value={formData.password} onChange={(e: ChangeEvent<HTMLInputElement>) => setFormData({...formData, password: e.target.value})} className="w-full border border-slate-200 rounded-lg px-4 py-2 outline-none focus:border-blue-500" placeholder="Minimal 6 karakter" minLength={6} />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Role</label>
                <select value={formData.role} onChange={(e: ChangeEvent<HTMLSelectElement>) => setFormData({...formData, role: e.target.value as UserCreateRequest['role']})} className="w-full border border-slate-200 rounded-lg px-4 py-2 outline-none focus:border-blue-500">
                  <option>Super Admin</option>
                  <option>CS Agent</option>
                  <option>Editor (Knowledge Base)</option>
                </select>
              </div>
              <div className="pt-4 flex gap-3">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-2.5 border border-slate-200 text-slate-600 font-medium rounded-xl hover:bg-slate-50 transition-colors">Batal</button>
                <button type="submit" className="flex-1 py-2.5 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors">Simpan</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;