'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import {
  encryptData,
  decryptData,
  validateMasterPassword,
  generateSecurePassword,
} from '@/lib/encryption';

interface VaultItem {
  id: string;
  platform_name: string;
  account_identifier: string;
  encrypted_api_key: string;
  encrypted_api_secret: string | null;
  encrypted_additional_data: string | null;
  encryption_iv: string;
  encryption_salt: string;
  key_type: string;
  environment: string;
  tags: string[];
  last_accessed_at: string | null;
  created_at: string;
  decrypted?: {
    apiKey?: string;
    apiSecret?: string;
    additionalData?: string;
  };
}

export default function VaultPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [masterPassword, setMasterPassword] = useState('');
  const [vaults, setVaults] = useState<VaultItem[]>([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [autoLockTimer, setAutoLockTimer] = useState<NodeJS.Timeout | null>(null);
  const [revealedKeys, setRevealedKeys] = useState<Set<string>>(new Set());

  const [newVault, setNewVault] = useState({
    platformName: '',
    accountIdentifier: '',
    apiKey: '',
    apiSecret: '',
    additionalData: '',
    keyType: 'api_key',
    environment: 'production',
    tags: [] as string[],
  });

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  const resetAutoLock = () => {
    if (autoLockTimer) clearTimeout(autoLockTimer);
    const timer = setTimeout(() => {
      lockVault();
    }, 5 * 60 * 1000);
    setAutoLockTimer(timer);
  };

  const lockVault = () => {
    setIsUnlocked(false);
    setMasterPassword('');
    setVaults([]);
    setRevealedKeys(new Set());
    if (autoLockTimer) clearTimeout(autoLockTimer);
  };

  const unlockVault = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const validation = validateMasterPassword(masterPassword);
      if (!validation.valid) {
        setError(validation.errors.join('. '));
        setLoading(false);
        return;
      }

      const response = await fetch(`/api/vault/list?userId=${user?.id}`);
      const data = await response.json();

      if (data.success) {
        setVaults(data.vaults);
        setIsUnlocked(true);
        resetAutoLock();
      }
    } catch (err) {
      setError('Failed to unlock vault');
    } finally {
      setLoading(false);
    }
  };

  const addToVault = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const encryptedKey = await encryptData(newVault.apiKey, masterPassword);
      const encryptedSecret = newVault.apiSecret
        ? await encryptData(newVault.apiSecret, masterPassword)
        : null;
      const encryptedAdditional = newVault.additionalData
        ? await encryptData(newVault.additionalData, masterPassword)
        : null;

      const response = await fetch('/api/vault/store', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: user?.id,
          platformName: newVault.platformName,
          accountIdentifier: newVault.accountIdentifier,
          encryptedApiKey: encryptedKey.encrypted,
          encryptedApiSecret: encryptedSecret?.encrypted,
          encryptedAdditionalData: encryptedAdditional?.encrypted,
          encryptionIv: encryptedKey.iv,
          encryptionSalt: encryptedKey.salt,
          keyType: newVault.keyType,
          environment: newVault.environment,
          tags: newVault.tags,
        }),
      });

      const data = await response.json();

      if (data.success) {
        const listResponse = await fetch(`/api/vault/list?userId=${user?.id}`);
        const listData = await listResponse.json();
        setVaults(listData.vaults);
        setShowAddForm(false);
        setNewVault({
          platformName: '',
          accountIdentifier: '',
          apiKey: '',
          apiSecret: '',
          additionalData: '',
          keyType: 'api_key',
          environment: 'production',
          tags: [],
        });
        resetAutoLock();
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to add to vault');
    } finally {
      setLoading(false);
    }
  };

  const revealKey = async (vault: VaultItem) => {
    try {
      const decryptedKey = await decryptData({
        encrypted: vault.encrypted_api_key,
        iv: vault.encryption_iv,
        salt: vault.encryption_salt,
        masterPassword,
      });

      const decryptedSecret = vault.encrypted_api_secret
        ? await decryptData({
            encrypted: vault.encrypted_api_secret,
            iv: vault.encryption_iv,
            salt: vault.encryption_salt,
            masterPassword,
          })
        : undefined;

      const updatedVaults = vaults.map((v) =>
        v.id === vault.id
          ? {
              ...v,
              decrypted: {
                apiKey: decryptedKey,
                apiSecret: decryptedSecret,
              },
            }
          : v
      );
      setVaults(updatedVaults);
      setRevealedKeys(new Set([...revealedKeys, vault.id]));
      resetAutoLock();
    } catch (err) {
      setError('Failed to decrypt: Invalid master password');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setTimeout(() => {
      navigator.clipboard.writeText('');
    }, 30000);
  };

  const deleteVault = async (vaultId: string) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;

    try {
      const response = await fetch('/api/vault/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vaultId, userId: user?.id }),
      });

      if (response.ok) {
        setVaults(vaults.filter((v) => v.id !== vaultId));
      }
    } catch (err) {
      setError('Failed to delete vault');
    }
  };

  if (!user) return null;

  if (!isUnlocked) {
    return (
      <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center px-6">
        <div className="max-w-md w-full bg-[#1a1a24] border border-zinc-800 rounded-2xl p-8">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🔐</div>
            <h1 className="text-3xl font-bold mb-2">Secure API Vault</h1>
            <p className="text-zinc-400 text-sm">
              Zero-Knowledge Encryption • NoTrust Architecture
            </p>
          </div>

          <form onSubmit={unlockVault} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-2">
                Master Password
              </label>
              <input
                type="password"
                value={masterPassword}
                onChange={(e) => setMasterPassword(e.target.value)}
                className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
                placeholder="Enter your master password"
                required
              />
              <p className="text-xs text-zinc-500 mt-2">
                Minimum 16 chars • Uppercase • Lowercase • Numbers • Symbols
              </p>
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500 rounded-lg p-3 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-700 rounded-lg font-medium transition-colors"
            >
              {loading ? 'Unlocking...' : 'Unlock Vault'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-zinc-800">
            <h3 className="text-sm font-semibold mb-3">Security Features</h3>
            <ul className="space-y-2 text-xs text-zinc-400">
              <li>✓ AES-256-GCM client-side encryption</li>
              <li>✓ 600,000 PBKDF2 iterations</li>
              <li>✓ Auto-lock after 5 minutes</li>
              <li>✓ Server never sees unencrypted keys</li>
              <li>✓ Full audit trail</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <header className="border-b border-zinc-800 bg-[#12121a] sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold">🔐 Secure API Vault</h1>
            <span className="px-3 py-1 bg-green-500/10 border border-green-500 rounded-full text-xs text-green-400">
              Unlocked
            </span>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="px-4 py-2 text-sm text-zinc-400 hover:text-white transition-colors"
            >
              Dashboard
            </button>
            <button
              onClick={lockVault}
              className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
            >
              Lock Vault
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold mb-2">Your API Keys</h2>
            <p className="text-zinc-400">
              {vaults.length} encrypted {vaults.length === 1 ? 'key' : 'keys'} stored
            </p>
          </div>
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors"
          >
            {showAddForm ? 'Cancel' : '+ Add API Key'}
          </button>
        </div>

        {showAddForm && (
          <form
            onSubmit={addToVault}
            className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6 mb-8 space-y-4"
          >
            <h3 className="text-lg font-semibold">Add New API Key</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Platform Name (e.g., Stripe, OpenAI)"
                value={newVault.platformName}
                onChange={(e) =>
                  setNewVault({ ...newVault, platformName: e.target.value })
                }
                className="px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
                required
              />
              <input
                type="text"
                placeholder="Account/Email (optional)"
                value={newVault.accountIdentifier}
                onChange={(e) =>
                  setNewVault({ ...newVault, accountIdentifier: e.target.value })
                }
                className="px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
              />
            </div>
            <input
              type="text"
              placeholder="API Key"
              value={newVault.apiKey}
              onChange={(e) => setNewVault({ ...newVault, apiKey: e.target.value })}
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
              required
            />
            <input
              type="text"
              placeholder="API Secret (optional)"
              value={newVault.apiSecret}
              onChange={(e) =>
                setNewVault({ ...newVault, apiSecret: e.target.value })
              }
              className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
            />
            <div className="grid md:grid-cols-2 gap-4">
              <select
                value={newVault.keyType}
                onChange={(e) => setNewVault({ ...newVault, keyType: e.target.value })}
                className="px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="api_key">API Key</option>
                <option value="oauth_token">OAuth Token</option>
                <option value="jwt">JWT</option>
                <option value="webhook_secret">Webhook Secret</option>
              </select>
              <select
                value={newVault.environment}
                onChange={(e) =>
                  setNewVault({ ...newVault, environment: e.target.value })
                }
                className="px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="production">Production</option>
                <option value="staging">Staging</option>
                <option value="development">Development</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-zinc-700 rounded-lg font-medium transition-colors"
            >
              {loading ? 'Encrypting & Storing...' : 'Add to Vault'}
            </button>
          </form>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500 rounded-lg p-4 mb-6 text-red-400">
            {error}
          </div>
        )}

        <div className="grid gap-4">
          {vaults.map((vault) => (
            <div
              key={vault.id}
              className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6 hover:border-indigo-500/50 transition-colors"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{vault.platform_name}</h3>
                  {vault.account_identifier && (
                    <p className="text-sm text-zinc-400">{vault.account_identifier}</p>
                  )}
                </div>
                <div className="flex gap-2">
                  <span className="px-3 py-1 bg-zinc-800 rounded-full text-xs">
                    {vault.key_type}
                  </span>
                  <span className="px-3 py-1 bg-zinc-800 rounded-full text-xs">
                    {vault.environment}
                  </span>
                </div>
              </div>

              {revealedKeys.has(vault.id) && vault.decrypted ? (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs text-zinc-400 mb-1">API Key</label>
                    <div className="flex gap-2">
                      <code className="flex-1 px-3 py-2 bg-[#0a0a0f] rounded text-sm text-green-400 break-all">
                        {vault.decrypted.apiKey}
                      </code>
                      <button
                        onClick={() => copyToClipboard(vault.decrypted!.apiKey!)}
                        className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-sm transition-colors"
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                  {vault.decrypted.apiSecret && (
                    <div>
                      <label className="block text-xs text-zinc-400 mb-1">
                        API Secret
                      </label>
                      <div className="flex gap-2">
                        <code className="flex-1 px-3 py-2 bg-[#0a0a0f] rounded text-sm text-green-400 break-all">
                          {vault.decrypted.apiSecret}
                        </code>
                        <button
                          onClick={() => copyToClipboard(vault.decrypted!.apiSecret!)}
                          className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 rounded text-sm transition-colors"
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => revealKey(vault)}
                  className="w-full py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm transition-colors"
                >
                  🔓 Reveal API Key
                </button>
              )}

              <div className="flex justify-between items-center mt-4 pt-4 border-t border-zinc-800">
                <span className="text-xs text-zinc-500">
                  Added {new Date(vault.created_at).toLocaleDateString()}
                </span>
                <button
                  onClick={() => deleteVault(vault.id)}
                  className="text-xs text-red-400 hover:text-red-300 transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}