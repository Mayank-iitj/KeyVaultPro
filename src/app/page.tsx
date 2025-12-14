import WorkflowDemo from '@/components/WorkflowDemo';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white">
      <header className="border-b border-zinc-800 bg-[#12121a] sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <a href="/" className="text-xl font-bold text-indigo-500">
            <span className="mr-2">🔐</span>
            <span className="text-white">API Key Manager</span>
          </a>
          <nav className="flex gap-6">
            <a href="#demo" className="text-zinc-400 hover:text-indigo-400 transition-colors">Live Demo</a>
            <a href="#features" className="text-zinc-400 hover:text-indigo-400 transition-colors">Features</a>
            <a href="#quickstart" className="text-zinc-400 hover:text-indigo-400 transition-colors">Quick Start</a>
            <a href="https://mayyanks.app" target="_blank" rel="noopener noreferrer" className="text-zinc-400 hover:text-indigo-400 transition-colors">Author</a>
          </nav>
        </div>
      </header>

      <section className="py-24 px-6 text-center bg-gradient-to-b from-[#12121a] to-[#0a0a0f]">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-indigo-500 to-purple-500 bg-clip-text text-transparent">
            API Key Management System
          </h1>
          <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto">
            A production-ready, secure API key management solution built entirely with Python. 
            Generate, rotate, and monitor your API keys with fine-grained permissions.
          </p>
          <div className="flex gap-4 justify-center flex-wrap">
            <a href="#demo" className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-medium transition-colors">
              Try Live Demo
            </a>
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="px-6 py-3 border border-zinc-700 hover:border-indigo-500 rounded-lg font-medium transition-colors">
              View on GitHub
            </a>
          </div>
        </div>
      </section>

      <WorkflowDemo />

      <section id="features" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: "🔑", title: "Secure Key Generation", desc: "Cryptographically secure API keys using Python's secrets module. Keys shown once and stored as SHA-256 hashes." },
              { icon: "🛡️", title: "Fine-Grained Permissions", desc: "Scope-based access control with read, write, delete, and admin permissions per key." },
              { icon: "🔄", title: "Key Rotation", desc: "Manual and automatic rotation with configurable grace periods for seamless transitions." },
              { icon: "📊", title: "Usage Monitoring", desc: "Comprehensive audit logs tracking every API key usage with IP, endpoint, and response times." },
              { icon: "⚡", title: "Rate Limiting", desc: "Token bucket algorithm with per-key and global limits. Auto-block on abuse." },
              { icon: "🤖", title: "AI Security Insights", desc: "Anomaly detection using statistical analysis to identify suspicious usage patterns." },
              { icon: "👥", title: "RBAC", desc: "Role-Based Access Control with Admin, Developer, and Read-Only roles." },
              { icon: "🔒", title: "Zero-Trust Design", desc: "Keys scoped to IP ranges, user agents, and environments (dev/staging/prod)." },
              { icon: "📱", title: "Python Dashboard", desc: "Admin dashboard built with Jinja2 templates. No JavaScript frameworks required." },
            ].map((feature, i) => (
              <div key={i} className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6 hover:border-indigo-500/50 transition-colors">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                <p className="text-zinc-400 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 px-6 bg-[#12121a]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-8">Tech Stack</h2>
          <div className="flex flex-wrap gap-3 justify-center">
            {["Python 3.10+", "FastAPI", "SQLAlchemy", "PostgreSQL/SQLite", "bcrypt", "Fernet+PBKDF2", "JWT", "Jinja2", "pytest"].map((tech) => (
              <span key={tech} className="px-4 py-2 bg-[#1a1a24] border border-zinc-800 rounded-lg text-sm text-zinc-300">
                {tech}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section id="quickstart" className="py-20 px-6">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Quick Start</h2>
          <div className="space-y-6">
            <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4">1. Register a User</h3>
              <pre className="bg-[#0a0a0f] p-4 rounded-lg overflow-x-auto text-sm text-green-400">
{`curl -X POST "http://localhost:8000/api/v1/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "username": "myuser", "password": "SecurePass123!"}'`}
              </pre>
            </div>
            <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4">2. Login to Get Token</h3>
              <pre className="bg-[#0a0a0f] p-4 rounded-lg overflow-x-auto text-sm text-green-400">
{`curl -X POST "http://localhost:8000/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'`}
              </pre>
            </div>
            <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4">3. Create an API Key</h3>
              <pre className="bg-[#0a0a0f] p-4 rounded-lg overflow-x-auto text-sm text-green-400">
{`curl -X POST "http://localhost:8000/api/v1/keys" \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name": "My API Key", "permissions": ["read", "write"]}'`}
              </pre>
            </div>
            <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4">4. Use the API Key</h3>
              <pre className="bg-[#0a0a0f] p-4 rounded-lg overflow-x-auto text-sm text-green-400">
{`curl -X GET "http://localhost:8000/api/v1/protected/test" \\
  -H "X-API-Key: akm_YOUR_API_KEY_HERE"`}
              </pre>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 px-6 bg-[#12121a]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-8">API Endpoints</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4 text-indigo-400">Authentication</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li><code className="text-green-400">POST</code> /api/v1/auth/register</li>
                <li><code className="text-green-400">POST</code> /api/v1/auth/login</li>
                <li><code className="text-green-400">POST</code> /api/v1/auth/refresh</li>
                <li><code className="text-green-400">POST</code> /api/v1/auth/logout</li>
                <li><code className="text-blue-400">GET</code> /api/v1/auth/me</li>
              </ul>
            </div>
            <div className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6">
              <h3 className="text-lg font-semibold mb-4 text-indigo-400">API Keys</h3>
              <ul className="space-y-2 text-sm text-zinc-400">
                <li><code className="text-green-400">POST</code> /api/v1/keys</li>
                <li><code className="text-blue-400">GET</code> /api/v1/keys</li>
                <li><code className="text-yellow-400">PUT</code> /api/v1/keys/{"{id}"}</li>
                <li><code className="text-red-400">DELETE</code> /api/v1/keys/{"{id}"}</li>
                <li><code className="text-green-400">POST</code> /api/v1/keys/{"{id}"}/rotate</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-6">Project Structure</h2>
          <pre className="bg-[#1a1a24] border border-zinc-800 rounded-xl p-6 text-left text-sm text-zinc-400 overflow-x-auto">
{`api-key-manager/
├── app/
│   ├── main.py              # FastAPI application
│   ├── auth/                # Authentication module
│   ├── keys/                # API Keys module
│   ├── middleware/          # Rate limiting & validation
│   ├── security/            # Encryption & hashing
│   ├── database/            # Models & connection
│   ├── logs/                # Audit logging
│   └── templates/           # Jinja2 templates
├── tests/                   # Test suite
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md`}
          </pre>
        </div>
      </section>

      <footer className="border-t border-zinc-800 py-12 px-6 text-center">
        <div className="max-w-4xl mx-auto">
          <p className="text-zinc-400 mb-2">
            Designed & Engineered by{" "}
            <a href="https://mayyanks.app" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:text-indigo-300 transition-colors">
              Mayank Sharma
            </a>
          </p>
          <p className="text-zinc-500 text-sm">
            API Key Management System v1.0.0 | Python Only | Production Ready
          </p>
        </div>
      </footer>
    </div>
  );
}