'use client';

import { useState } from 'react';

interface DemoStep {
  id: number;
  title: string;
  status: 'pending' | 'loading' | 'success' | 'error';
  description?: string;
  code?: string;
  response?: any;
}

export default function WorkflowDemo() {
  const [steps, setSteps] = useState<DemoStep[]>([
    { id: 1, title: 'Register User', status: 'pending' },
    { id: 2, title: 'Login & Get Token', status: 'pending' },
    { id: 3, title: 'Set PIN for Key Security', status: 'pending' },
    { id: 4, title: 'Create API Key', status: 'pending' },
    { id: 5, title: 'Verify PIN to View Key', status: 'pending' },
    { id: 6, title: 'Test Protected Endpoint', status: 'pending' },
  ]);

  const [userId, setUserId] = useState<string>('');
  const [apiKeyId, setApiKeyId] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [pin, setPin] = useState<string>('');
  const [isRunning, setIsRunning] = useState(false);
  const [randomEmail, setRandomEmail] = useState('');
  const [randomUsername, setRandomUsername] = useState('');
  const [randomPassword, setRandomPassword] = useState('');

  const updateStep = (id: number, updates: Partial<DemoStep>) => {
    setSteps(prev => prev.map(step => 
      step.id === id ? { ...step, ...updates } : step
    ));
  };

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const generateRandomCredentials = () => {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 8);
    return {
      email: `user_${random}_${timestamp}@demo.com`,
      username: `user_${random}`,
      password: `Pass${random}123!`,
      pin: Math.floor(100000 + Math.random() * 900000).toString(),
    };
  };

  const generateApiKey = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let key = 'akm_';
    for (let i = 0; i < 32; i++) {
      key += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return key;
  };

  const runDemo = async () => {
    setIsRunning(true);
    
    try {
      const credentials = generateRandomCredentials();
      setRandomEmail(credentials.email);
      setRandomUsername(credentials.username);
      setRandomPassword(credentials.password);
      setPin(credentials.pin);

      updateStep(1, { status: 'loading', description: 'Registering new user with randomized credentials...' });
      await sleep(800);
      
      const registerRes = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: credentials.email,
          username: credentials.username,
          password: credentials.password,
        }),
      });
      
      if (!registerRes.ok) {
        const error = await registerRes.json();
        throw new Error(error.error || 'Registration failed');
      }
      
      const userData = await registerRes.json();
      setUserId(userData.id);
      
      updateStep(1, { 
        status: 'success', 
        description: `User registered: ${credentials.email}`,
        code: `Email: ${credentials.email}\nUsername: ${credentials.username}\nPassword: ${credentials.password}`,
        response: { id: userData.id, email: userData.email, username: userData.username }
      });
      
      await sleep(1000);
      
      updateStep(2, { status: 'loading', description: 'Authenticating user...' });
      await sleep(800);
      
      const loginRes = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: credentials.email,
          password: credentials.password,
        }),
      });
      
      if (!loginRes.ok) {
        const error = await loginRes.json();
        throw new Error(error.error || 'Login failed');
      }
      
      const loginData = await loginRes.json();
      
      updateStep(2, { 
        status: 'success', 
        description: `Logged in as ${credentials.email}`,
        code: `User ID: ${loginData.user_id}\nRole: ${loginData.role}`,
        response: { user_id: loginData.user_id, email: loginData.email, role: loginData.role }
      });
      
      await sleep(1000);
      
      updateStep(3, { status: 'loading', description: 'Setting up PIN for key protection...' });
      await sleep(800);
      
      updateStep(3, { 
        status: 'success', 
        description: `6-digit PIN generated: ${credentials.pin}`,
        code: `PIN: ${credentials.pin}\n(This PIN will be required to view the API key)`,
        response: { pin_set: true, pin_length: 6 }
      });
      
      await sleep(1000);
      
      updateStep(4, { status: 'loading', description: 'Creating encrypted API key...' });
      await sleep(1000);
      
      const generatedKey = generateApiKey();
      
      const createKeyRes = await fetch('/api/keys/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId: userData.id,
          name: `Demo Key ${new Date().toLocaleTimeString()}`,
          apiKey: generatedKey,
          pin: credentials.pin,
          permissions: ['read', 'write'],
        }),
      });
      
      if (!createKeyRes.ok) {
        const error = await createKeyRes.json();
        throw new Error(error.error || 'Key creation failed');
      }
      
      const keyData = await createKeyRes.json();
      setApiKeyId(keyData.id);
      setApiKey(generatedKey);
      
      updateStep(4, { 
        status: 'success', 
        description: `API Key created and encrypted!`,
        code: `Key ID: ${keyData.id}\nPreview: ${keyData.preview}\nPermissions: ${keyData.permissions.join(', ')}`,
        response: { 
          id: keyData.id, 
          name: keyData.name, 
          preview: keyData.preview,
          permissions: keyData.permissions,
          message: '🔒 Full key hidden - PIN required to view'
        }
      });
      
      await sleep(1000);
      
      updateStep(5, { status: 'loading', description: 'Verifying PIN to reveal API key...' });
      await sleep(1200);
      
      const verifyPinRes = await fetch('/api/keys/verify-pin', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyId: keyData.id,
          pin: credentials.pin,
          userId: userData.id,
        }),
      });
      
      if (!verifyPinRes.ok) {
        const error = await verifyPinRes.json();
        throw new Error(error.error || 'PIN verification failed');
      }
      
      const pinVerifyData = await verifyPinRes.json();
      
      updateStep(5, { 
        status: 'success', 
        description: `✅ PIN verified! API key revealed`,
        code: `Full API Key: ${generatedKey}`,
        response: { 
          pin_verified: true, 
          api_key: generatedKey,
          key_id: keyData.id,
          message: '✅ PIN authentication successful'
        }
      });
      
      await sleep(1000);
      
      updateStep(6, { status: 'loading', description: 'Testing API key with protected endpoint...' });
      await sleep(800);
      
      const testKeyRes = await fetch('/api/keys/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keyId: keyData.id,
          apiKey: generatedKey,
          userId: userData.id,
        }),
      });
      
      if (!testKeyRes.ok) {
        const error = await testKeyRes.json();
        throw new Error(error.error || 'API key test failed');
      }
      
      const testData = await testKeyRes.json();
      
      updateStep(6, { 
        status: 'success', 
        description: '🎉 Protected endpoint accessed successfully!',
        code: `GET /api/protected/test\nX-API-Key: ${generatedKey.substring(0, 20)}...`,
        response: { 
          success: true, 
          message: 'API key validated',
          user_id: userData.id,
          permissions: testData.permissions,
          timestamp: testData.timestamp
        }
      });
      
    } catch (error: any) {
      console.error('Demo error:', error);
      setSteps(prev => prev.map(step => 
        step.status === 'loading' ? { ...step, status: 'error', description: error.message } : step
      ));
    } finally {
      setIsRunning(false);
    }
  };

  const resetDemo = () => {
    setSteps([
      { id: 1, title: 'Register User', status: 'pending' },
      { id: 2, title: 'Login & Get Token', status: 'pending' },
      { id: 3, title: 'Set PIN for Key Security', status: 'pending' },
      { id: 4, title: 'Create API Key', status: 'pending' },
      { id: 5, title: 'Verify PIN to View Key', status: 'pending' },
      { id: 6, title: 'Test Protected Endpoint', status: 'pending' },
    ]);
    setUserId('');
    setApiKeyId('');
    setApiKey('');
    setPin('');
    setRandomEmail('');
    setRandomUsername('');
    setRandomPassword('');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏸️';
      case 'loading': return '⏳';
      case 'success': return '✅';
      case 'error': return '❌';
      default: return '⏸️';
    }
  };

  return (
    <section id="demo" className="py-20 px-6 bg-gradient-to-b from-[#12121a] to-[#0a0a0f]">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
            🚀 Live Workflow Demo
          </h2>
          <p className="text-zinc-400 text-lg mb-6">
            Watch the complete API key lifecycle with PIN authentication
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={runDemo}
              disabled={isRunning}
              className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:from-zinc-700 disabled:to-zinc-800 rounded-lg font-medium transition-all transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed"
            >
              {isRunning ? '⏳ Running Demo...' : '▶️ Run Complete Demo'}
            </button>
            <button
              onClick={resetDemo}
              disabled={isRunning}
              className="px-6 py-3 border border-zinc-700 hover:border-indigo-500 disabled:border-zinc-800 rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
            >
              🔄 Reset
            </button>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {steps.map((step, index) => (
            <div
              key={step.id}
              className={`bg-[#1a1a24] border rounded-xl p-6 transition-all duration-300 ${
                step.status === 'loading' ? 'border-indigo-500 shadow-lg shadow-indigo-500/20' :
                step.status === 'success' ? 'border-green-500/50' :
                step.status === 'error' ? 'border-red-500/50' :
                'border-zinc-800'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="text-3xl flex-shrink-0">
                  {getStatusIcon(step.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                    <span className="text-zinc-500">Step {index + 1}:</span>
                    <span className="text-white">{step.title}</span>
                  </h3>
                  
                  {step.description && (
                    <p className="text-sm text-zinc-400 mb-3">{step.description}</p>
                  )}
                  
                  {step.code && (
                    <details className="mb-3">
                      <summary className="text-sm text-indigo-400 cursor-pointer hover:text-indigo-300 mb-2">
                        View details
                      </summary>
                      <pre className="bg-[#0a0a0f] p-3 rounded-lg overflow-x-auto text-xs text-green-400 whitespace-pre-wrap break-all">
                        {step.code}
                      </pre>
                    </details>
                  )}
                  
                  {step.response && (
                    <details>
                      <summary className="text-sm text-indigo-400 cursor-pointer hover:text-indigo-300 mb-2">
                        View response
                      </summary>
                      <pre className="bg-[#0a0a0f] p-3 rounded-lg overflow-x-auto text-xs text-zinc-400 max-h-32">
                        {JSON.stringify(step.response, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {(randomEmail || apiKey) && (
          <div className="mt-8 bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4 text-indigo-400">🔑 Session Credentials</h3>
            <div className="space-y-3">
              {randomEmail && (
                <div>
                  <label className="text-sm text-zinc-500 block mb-1">Email:</label>
                  <code className="text-xs bg-[#0a0a0f] p-2 rounded block overflow-x-auto text-green-400">
                    {randomEmail}
                  </code>
                </div>
              )}
              {randomPassword && (
                <div>
                  <label className="text-sm text-zinc-500 block mb-1">Password:</label>
                  <code className="text-xs bg-[#0a0a0f] p-2 rounded block overflow-x-auto text-green-400">
                    {randomPassword}
                  </code>
                </div>
              )}
              {pin && (
                <div>
                  <label className="text-sm text-zinc-500 block mb-1">PIN (for viewing API key):</label>
                  <code className="text-xs bg-[#0a0a0f] p-2 rounded block overflow-x-auto text-yellow-400">
                    {pin}
                  </code>
                </div>
              )}
              {apiKey && (
                <div>
                  <label className="text-sm text-zinc-500 block mb-1">Generated API Key:</label>
                  <code className="text-xs bg-[#0a0a0f] p-2 rounded block overflow-x-auto text-green-400 break-all">
                    {apiKey}
                  </code>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
