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
    { id: 3, title: 'Create API Key', status: 'pending' },
    { id: 4, title: 'Test Protected Endpoint', status: 'pending' },
    { id: 5, title: 'View API Keys', status: 'pending' },
    { id: 6, title: 'Rotate API Key', status: 'pending' },
  ]);

  const [token, setToken] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [keyId, setKeyId] = useState<string>('');
  const [isRunning, setIsRunning] = useState(false);
  const [email] = useState(`demo${Date.now()}@example.com`);
  const [password] = useState('DemoPass123!');

  const updateStep = (id: number, updates: Partial<DemoStep>) => {
    setSteps(prev => prev.map(step => 
      step.id === id ? { ...step, ...updates } : step
    ));
  };

  const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const runDemo = async () => {
    setIsRunning(true);
    
    try {
      // Step 1: Register User
      updateStep(1, { status: 'loading', description: 'Registering new user...' });
      await sleep(500);
      
      const registerResponse = await fetch('/api/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: '/api/v1/auth/register',
          method: 'POST',
          body: {
            email,
            username: `demo${Date.now()}`,
            password,
          }
        })
      });
      
      const registerData = await registerResponse.json();
      
      if (registerResponse.ok) {
        updateStep(1, { 
          status: 'success', 
          description: `User registered: ${registerData.email}`,
          code: `curl -X POST "http://localhost:8000/api/v1/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "${email}", "username": "demo", "password": "${password}"}'`,
          response: registerData
        });
      } else {
        throw new Error(registerData.detail || 'Registration failed');
      }
      
      await sleep(1000);
      
      // Step 2: Login
      updateStep(2, { status: 'loading', description: 'Logging in...' });
      await sleep(500);
      
      const loginResponse = await fetch('/api/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: '/api/v1/auth/login',
          method: 'POST',
          body: { email, password }
        })
      });
      
      const loginData = await loginResponse.json();
      
      if (loginResponse.ok) {
        setToken(loginData.access_token);
        updateStep(2, { 
          status: 'success', 
          description: `JWT Token acquired: ${loginData.access_token.substring(0, 30)}...`,
          code: `curl -X POST "http://localhost:8000/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "${email}", "password": "${password}"}'`,
          response: { ...loginData, access_token: loginData.access_token.substring(0, 50) + '...' }
        });
      } else {
        throw new Error(loginData.detail || 'Login failed');
      }
      
      await sleep(1000);
      
      // Step 3: Create API Key
      updateStep(3, { status: 'loading', description: 'Creating API key...' });
      await sleep(500);
      
      const createKeyResponse = await fetch('/api/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: '/api/v1/keys',
          method: 'POST',
          headers: { 'Authorization': `Bearer ${loginData.access_token}` },
          body: {
            name: 'Demo Key',
            permissions: ['read', 'write']
          }
        })
      });
      
      const keyData = await createKeyResponse.json();
      
      if (createKeyResponse.ok) {
        setApiKey(keyData.api_key);
        setKeyId(keyData.id);
        updateStep(3, { 
          status: 'success', 
          description: `API Key created: ${keyData.key_prefix}...`,
          code: `curl -X POST "http://localhost:8000/api/v1/keys" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Demo Key", "permissions": ["read", "write"]}'`,
          response: { ...keyData, api_key: keyData.api_key.substring(0, 30) + '...' }
        });
      } else {
        throw new Error(keyData.detail || 'Key creation failed');
      }
      
      await sleep(1000);
      
      // Step 4: Test Protected Endpoint
      updateStep(4, { status: 'loading', description: 'Testing API key...' });
      await sleep(500);
      
      const testResponse = await fetch('/api/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: '/api/v1/protected/test',
          method: 'GET',
          headers: { 'X-API-Key': keyData.api_key }
        })
      });
      
      const testData = await testResponse.json();
      
      if (testResponse.ok) {
        updateStep(4, { 
          status: 'success', 
          description: 'Protected endpoint accessed successfully!',
          code: `curl -X GET "http://localhost:8000/api/v1/protected/test" \\
  -H "X-API-Key: ${keyData.api_key.substring(0, 20)}..."`,
          response: testData
        });
      } else {
        throw new Error(testData.detail || 'API key test failed');
      }
      
      await sleep(1000);
      
      // Step 5: View API Keys
      updateStep(5, { status: 'loading', description: 'Fetching all API keys...' });
      await sleep(500);
      
      const listResponse = await fetch('/api/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: '/api/v1/keys',
          method: 'GET',
          headers: { 'Authorization': `Bearer ${loginData.access_token}` }
        })
      });
      
      const listData = await listResponse.json();
      
      if (listResponse.ok) {
        updateStep(5, { 
          status: 'success', 
          description: `Found ${listData.length} API key(s)`,
          code: `curl -X GET "http://localhost:8000/api/v1/keys" \\
  -H "Authorization: Bearer YOUR_TOKEN"`,
          response: listData
        });
      } else {
        throw new Error(listData.detail || 'Failed to list keys');
      }
      
      await sleep(1000);
      
      // Step 6: Rotate API Key
      updateStep(6, { status: 'loading', description: 'Rotating API key...' });
      await sleep(500);
      
      const rotateResponse = await fetch('/api/proxy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint: `/api/v1/keys/${keyData.id}/rotate`,
          method: 'POST',
          headers: { 'Authorization': `Bearer ${loginData.access_token}` },
          body: { grace_period_hours: 1 }
        })
      });
      
      const rotateData = await rotateResponse.json();
      
      if (rotateResponse.ok) {
        updateStep(6, { 
          status: 'success', 
          description: 'API key rotated successfully!',
          code: `curl -X POST "http://localhost:8000/api/v1/keys/${keyData.id}/rotate" \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -d '{"grace_period_hours": 1}'`,
          response: { ...rotateData, new_api_key: rotateData.new_api_key?.substring(0, 30) + '...' }
        });
      } else {
        throw new Error(rotateData.detail || 'Key rotation failed');
      }
      
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
      { id: 3, title: 'Create API Key', status: 'pending' },
      { id: 4, title: 'Test Protected Endpoint', status: 'pending' },
      { id: 5, title: 'View API Keys', status: 'pending' },
      { id: 6, title: 'Rotate API Key', status: 'pending' },
    ]);
    setToken('');
    setApiKey('');
    setKeyId('');
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
            Watch the entire API key lifecycle in action
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
                        View cURL command
                      </summary>
                      <pre className="bg-[#0a0a0f] p-3 rounded-lg overflow-x-auto text-xs text-green-400">
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

        {(token || apiKey) && (
          <div className="mt-8 bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
            <h3 className="text-lg font-semibold mb-4 text-indigo-400">🔑 Session Credentials</h3>
            <div className="space-y-3">
              {token && (
                <div>
                  <label className="text-sm text-zinc-500 block mb-1">JWT Access Token:</label>
                  <code className="text-xs bg-[#0a0a0f] p-2 rounded block overflow-x-auto text-green-400">
                    {token.substring(0, 80)}...
                  </code>
                </div>
              )}
              {apiKey && (
                <div>
                  <label className="text-sm text-zinc-500 block mb-1">Generated API Key:</label>
                  <code className="text-xs bg-[#0a0a0f] p-2 rounded block overflow-x-auto text-green-400">
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