import { useState, useEffect, useRef, ChangeEvent } from 'react';
import { UploadCloud, FileText, Trash2, RefreshCw, CheckCircle, AlertTriangle, Download } from 'lucide-react';
import api, { ApiError } from '../lib/apiClient';
import type { KBFile } from '../types/api';

interface SyncStatus {
  type: 'success' | 'warning' | 'error';
  message: string;
}

const KnowledgeBase = () => {
  const [files, setFiles] = useState<KBFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchFiles = () => {
    api.authGet<KBFile[]>('/api/admin/kb/files')
      .then(data => setFiles(data))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchFiles();
  }, []);

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.md') && !file.name.endsWith('.txt') && !file.name.endsWith('.pdf')) {
      alert('Hanya file .txt, .md, atau .pdf yang didukung');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    try {
      await api.authUpload('/api/admin/kb/upload', formData);
      fetchFiles();
      setSyncStatus({ type: 'warning', message: 'Ada dokumen baru. Harap lakukan sinkronisasi (Re-Index).' });
    } catch (err) {
      if (err instanceof ApiError) {
        alert(`Gagal: ${err.message}`);
      } else {
        console.error(err);
        alert('Terjadi kesalahan saat mengunggah file.');
      }
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDelete = async (filename: string) => {
    if (!confirm(`Hapus ${filename}?`)) return;
    
    try {
      await api.authDelete(`/api/admin/kb/files/${filename}`);
      fetchFiles();
      setSyncStatus({ type: 'warning', message: 'Dokumen dihapus. Harap lakukan sinkronisasi (Re-Index).' });
    } catch (err) {
      console.error(err);
    }
  };

  const handleReindex = async () => {
    setIsSyncing(true);
    setSyncStatus(null);
    try {
      await api.authPost('/api/admin/kb/reindex');
      setSyncStatus({ type: 'success', message: 'Sinkronisasi berhasil! Bot kini menggunakan data terbaru.' });
    } catch (err) {
      console.error(err);
      setSyncStatus({ type: 'error', message: 'Gagal melakukan sinkronisasi.' });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleExport = async () => {
    const token = localStorage.getItem('lexa_admin_token');
    const exportApiUrl = window.__LEXA_CONFIG__?.apiUrl || window.location.origin;
    try {
      const res = await fetch(`${exportApiUrl}/api/admin/kb/export`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'lexa_kb_export.zip';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert('Gagal mengunduh knowledge base.');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-800">Knowledge Base</h1>
        <p className="text-slate-500">Kelola dokumen sumber pengetahuan untuk bot Lexa.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Kiri: Daftar File & Status */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="font-semibold text-lg text-slate-800 mb-4">Dokumen Aktif ({files.length})</h2>
            
            <div className="space-y-3">
              {files.length === 0 ? (
                <div className="text-center p-8 border-2 border-dashed border-slate-200 rounded-xl text-slate-400">
                  <FileText className="w-12 h-12 mx-auto mb-2 text-slate-300" />
                  <p>Belum ada dokumen referensi.</p>
                </div>
              ) : (
                files.map((file, i) => (
                  <div key={i} className="flex items-center justify-between p-4 bg-slate-50 border border-slate-100 rounded-xl hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3">
                      <div className="bg-blue-100 p-2 rounded-lg">
                        <FileText className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-700 text-sm">{file.filename}</p>
                        <p className="text-xs text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <button 
                      onClick={() => handleDelete(file.filename)}
                      className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Hapus Dokumen"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Kanan: Aksi (Upload & Sync) */}
        <div className="space-y-6">
          
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="font-semibold text-lg text-slate-800 mb-4">Unggah Dokumen</h2>
            
            <div 
              className="border-2 border-dashed border-blue-200 bg-blue-50/50 hover:bg-blue-50 p-6 rounded-xl text-center cursor-pointer transition-colors relative"
              onClick={() => fileInputRef.current?.click()}
            >
              {isUploading ? (
                <div className="animate-pulse">
                  <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto mb-2"></div>
                  <p className="text-sm text-blue-600 font-medium">Mengunggah...</p>
                </div>
              ) : (
                <>
                  <UploadCloud className="w-10 h-10 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm font-medium text-blue-700">Pilih File (PDF, TXT, MD)</p>
                  <p className="text-xs text-slate-500 mt-1">atau seret dan lepas di sini</p>
                </>
              )}
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden" 
                accept=".txt,.md,.pdf"
                onChange={handleFileUpload}
              />
            </div>
          </div>

          <div className="bg-slate-900 rounded-2xl shadow-lg p-6 relative overflow-hidden">
            <div className="absolute -top-10 -right-10 w-32 h-32 bg-blue-500/20 blur-3xl rounded-full"></div>
            <h2 className="font-semibold text-lg text-white mb-2 relative z-10">Sinkronisasi AI</h2>
            <p className="text-sm text-slate-300 mb-6 relative z-10">Latih ulang model RAG dengan semua dokumen yang ada di daftar.</p>
            
            {syncStatus && (
              <div className={`p-3 rounded-lg mb-4 text-xs font-medium flex gap-2 ${
                syncStatus.type === 'success' ? 'bg-green-500/20 text-green-300 border border-green-500/30' :
                syncStatus.type === 'warning' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                'bg-red-500/20 text-red-300 border border-red-500/30'
              }`}>
                {syncStatus.type === 'success' ? <CheckCircle className="w-4 h-4 shrink-0" /> : <AlertTriangle className="w-4 h-4 shrink-0" />}
                {syncStatus.message}
              </div>
            )}

            <div className="my-4">
              <button
                onClick={handleExport}
                className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2 shadow-md"
                title="Download semua dokumen sebagai ZIP"
              >
                <Download className="w-4 h-4" /> Download Semua Dokumen
              </button>
            </div>

            <button 
              onClick={handleReindex}
              disabled={isSyncing}
              className="w-full py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-medium rounded-xl transition-colors flex items-center justify-center gap-2 relative z-10"
            >
              <RefreshCw className={`w-5 h-5 ${isSyncing ? 'animate-spin' : ''}`} />
              {isSyncing ? 'Memproses Ulang (Re-Index)...' : 'Sinkronisasi Sekarang'}
            </button>
          </div>

        </div>

      </div>
    </div>
  );
};

export default KnowledgeBase;