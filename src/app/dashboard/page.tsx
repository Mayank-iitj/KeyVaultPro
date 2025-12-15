'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

interface ApiKey {
  id: string;
  name: string;
  key_preview: string;
  permissions: string[];
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  expires_at: string | null;
}

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loadingKeys, setLoadingKeys] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyPermissions, setNewKeyPermissions] = useState<string[]>(['read']);
  const [newKeyPin, setNewKeyPin] = useState('');
  const [createdKey, setCreatedKey] = useState<{ key: string; preview: string } | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (user) {
      loadApiKeys();
    }
  }, [user]);

  const loadApiKeys = async () => {
    try {
      const response = await fetch(`/api/keys/list?userId=${user?.id}`);
      const data = await response.json();
      if (response.ok) {
        setApiKeys(data.keys || []);
      }
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoadingKeys(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!/^\d{6}$/.test(newKeyPin)) {
      alert('PIN must be 6 digits');
      return;
    }

    try {
      const apiKey = `akm_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
      
      const response = await fetch('/api/keys/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user?.id,
          name: newKeyName,
          apiKey,
          pin: newKeyPin,
          permissions: newKeyPermissions,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        setCreatedKey({ key: apiKey, preview: data.key.key_preview });
        setNewKeyName('');
        setNewKeyPin('');
        setNewKeyPermissions(['read']);
        loadApiKeys();
      } else {
        alert(data.error || 'Failed to create API key');
      }
    } catch (error) {
      alert('Failed to create API key');
    }
  };

  const togglePermission = (perm: string) => {
    setNewKeyPermissions(prev =>
      prev.includes(perm) ? prev.filter(p => p !== perm) : [...prev, perm]
    );
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center">
        <div className="text-zinc-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <header className="border-b border-zinc-800 bg-[#12121a]">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="text-xl font-bold">
            <span className="mr-2">🔐</span>
            <span>API Key Manager</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-sm text-zinc-400">
              Welcome, <span className="text-white font-medium">{user.username}</span>
            </div>
            <button
              onClick={() => router.push('/vault')}
              className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
            >
              🔐 Secure Vault
            </button>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm text-zinc-400 hover:text-white border border-zinc-700 hover:border-zinc-500 rounded-lg transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Your API Keys</h1>
            <p className="text-zinc-400">Manage and monitor your API keys</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
          >
            + Create New Key
          </button>
        </div>

        {loadingKeys ? (
          <div className="text-center text-zinc-400 py-12">Loading keys...</div>
        ) : apiKeys.length === 0 ? (
          <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-12 text-center">
            <div className="text-5xl mb-4">🔑</div>
            <h3 className="text-xl font-semibold mb-2">No API Keys Yet</h3>
            <p className="text-zinc-400 mb-6">Create your first API key to get started</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
            >
              Create Your First Key
            </button>
          </div>
        ) : (
          <div className="grid gap-6">
            {apiKeys.map((key) => (
              <div key={key.id} className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold mb-1">{key.name}</h3>
                    <p className="text-sm text-zinc-400 font-mono">{key.key_preview}</p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium ${
                      key.is_active ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                    }`}
                  >
                    {key.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 mb-4">
                  {key.permissions.map((perm) => (
                    <span
                      key={perm}
                      className="px-3 py-1 bg-indigo-500/10 text-indigo-400 rounded-lg text-xs font-medium"
                    >
                      {perm}
                    </span>
                  ))}
                </div>
                <div className="text-xs text-zinc-500">
                  Created: {new Date(key.created_at).toLocaleDateString()} •{' '}
                  {key.last_used_at
                    ? `Last used: ${new Date(key.last_used_at).toLocaleDateString()}`
                    : 'Never used'}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-6 z-50">
          <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-6">Create New API Key</h2>
            <form onSubmit={handleCreateKey} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">Key Name</label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                  className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg focus:outline-none focus:border-indigo-500"
                  placeholder="Production API Key"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-2">6-Digit PIN</label>
                <input
                  type="text"
                  value={newKeyPin}
                  onChange={(e) => setNewKeyPin(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  pattern="\d{6}"
                  className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg focus:outline-none focus:border-indigo-500"
                  placeholder="123456"
                />
                <p className="text-xs text-zinc-500 mt-1">Required to view the full key later</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-3">Permissions</label>
                <div className="space-y-2">
                  {['read', 'write', 'delete', 'admin'].map((perm) => (
                    <label key={perm} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newKeyPermissions.includes(perm)}
                        onChange={() => togglePermission(perm)}
                        className="w-4 h-4"
                      />
                      <span className="text-sm capitalize">{perm}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewKeyName('');
                    setNewKeyPin('');
                    setNewKeyPermissions(['read']);
                  }}
                  className="flex-1 px-4 py-3 border border-zinc-700 hover:border-zinc-500 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
                >
                  Create Key
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {createdKey && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-6 z-50">
          <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-8 max-w-md w-full">
            <h2 className="text-2xl font-bold mb-4">API Key Created!</h2>
            <div className="bg-yellow-500/10 border border-yellow-500/50 text-yellow-400 px-4 py-3 rounded-lg text-sm mb-6">
              ⚠️ Save this key now! You won&apos;t be able to see it again without your PIN.
            </div>
            <div className="bg-[#0a0a0f] border border-zinc-700 rounded-lg p-4 mb-6">
              <p className="text-xs text-zinc-500 mb-2">Your API Key:</p>
              <p className="font-mono text-sm break-all text-green-400">{createdKey.key}</p>
            </div>
            <button
              onClick={() => {
                setCreatedKey(null);
                setShowCreateModal(false);
              }}
              className="w-full px-4 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
            >
              Got it!
            </button>
          </div>
        </div>
      )}
    </div>
  );
}