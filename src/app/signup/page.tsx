'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { signup } = useAuth();

  const validatePassword = (pwd: string) => {
    const minLength = pwd.length >= 8;
    const hasUpper = /[A-Z]/.test(pwd);
    const hasLower = /[a-z]/.test(pwd);
    const hasNumber = /[0-9]/.test(pwd);
    const hasSpecial = /[!@#$%^&*]/.test(pwd);

    return { minLength, hasUpper, hasLower, hasNumber, hasSpecial };
  };

  const passwordStrength = validatePassword(password);
  const isPasswordValid = Object.values(passwordStrength).every(Boolean);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!isPasswordValid) {
      setError('Password does not meet requirements');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    const result = await signup(email, username, password);

    if (result.success) {
      router.push('/dashboard');
    } else {
      setError(result.error || 'Signup failed');
    }

    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-block text-3xl font-bold text-indigo-500 mb-2">
            🔐 API Key Manager
          </Link>
          <h1 className="text-2xl font-bold mt-4">Create Account</h1>
          <p className="text-zinc-400 mt-2">Start managing your API keys securely</p>
        </div>

        <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-zinc-300 mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg focus:outline-none focus:border-indigo-500 text-white"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="username" className="block text-sm font-medium text-zinc-300 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg focus:outline-none focus:border-indigo-500 text-white"
                placeholder="johndoe"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-zinc-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg focus:outline-none focus:border-indigo-500 text-white"
                placeholder="••••••••"
              />
              {password && (
                <div className="mt-3 space-y-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className={passwordStrength.minLength ? 'text-green-400' : 'text-zinc-500'}>
                      {passwordStrength.minLength ? '✓' : '○'} 8+ characters
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={passwordStrength.hasUpper ? 'text-green-400' : 'text-zinc-500'}>
                      {passwordStrength.hasUpper ? '✓' : '○'} Uppercase letter
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={passwordStrength.hasLower ? 'text-green-400' : 'text-zinc-500'}>
                      {passwordStrength.hasLower ? '✓' : '○'} Lowercase letter
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={passwordStrength.hasNumber ? 'text-green-400' : 'text-zinc-500'}>
                      {passwordStrength.hasNumber ? '✓' : '○'} Number
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className={passwordStrength.hasSpecial ? 'text-green-400' : 'text-zinc-500'}>
                      {passwordStrength.hasSpecial ? '✓' : '○'} Special character (!@#$%^&*)
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-zinc-300 mb-2">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-[#0a0a0f] border border-zinc-700 rounded-lg focus:outline-none focus:border-indigo-500 text-white"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !isPasswordValid}
              className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-600/50 rounded-lg font-medium transition-colors"
            >
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-zinc-400 text-sm">
              Already have an account?{' '}
              <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
