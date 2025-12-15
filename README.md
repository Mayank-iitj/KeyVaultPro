# API Key Manager - Next.js Frontend

A production-ready API key management system with PIN authentication, built with Next.js and Supabase.

## Features

- 🔐 **Secure User Registration & Authentication**
- 🔑 **API Key Generation with bcrypt encryption**
- 📌 **PIN-Protected Key Viewing** - Keys hidden until PIN verified
- 🎲 **Randomized Demo Credentials** - New credentials each run
- 📊 **Comprehensive Audit Logging**
- 🗄️ **Supabase PostgreSQL Database**
- ✅ **Deployment Ready** - Configured for Vercel

## Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript
- **Database**: Supabase (PostgreSQL)
- **Authentication**: bcrypt password hashing
- **Styling**: Tailwind CSS
- **Deployment**: Vercel

## Getting Started

### Prerequisites

- Node.js 18+ or Bun
- Supabase account and project

### Installation

1. Clone the repository
2. Install dependencies:
```bash
npm install
# or
bun install
```

3. Set up environment variables:
```bash
cp .env.example .env.local
```

4. Add your Supabase credentials to `.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
DATABASE_URL=your_database_connection_string
```

5. Run the development server:
```bash
npm run dev
# or
bun dev
```

6. Open [http://localhost:3000](http://localhost:3000)

## Database Schema

The application uses three main tables:

### `users`
- User accounts with bcrypt-hashed passwords
- Email and username uniqueness
- Role-based access control

### `api_keys`
- Encrypted API keys (stored as bcrypt hashes)
- PIN protection for viewing keys
- Permissions and expiration tracking
- Last usage timestamps

### `audit_logs`
- Complete audit trail of all actions
- IP address and user agent tracking
- JSON metadata for detailed context

## Live Demo Workflow

The demo showcases:

1. **User Registration** - Randomized credentials each run
2. **Authentication** - Password verification with bcrypt
3. **PIN Setup** - 6-digit PIN generation for key protection
4. **API Key Creation** - Cryptographically secure key generation
5. **PIN Verification** - Keys hidden until PIN is verified
6. **Protected Endpoint Test** - API key validation

## Deployment

### Vercel Deployment

1. Push to GitHub
2. Connect repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy automatically on push

Environment variables needed:
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`

## Security Features

- ✅ Passwords hashed with bcrypt (10 rounds)
- ✅ API keys stored as bcrypt hashes
- ✅ PIN-protected key viewing
- ✅ Comprehensive audit logging
- ✅ SQL injection protection via Supabase
- ✅ Environment variable management
- ✅ No keys exposed in responses

## Project Structure

```
├── src/
│   ├── app/
│   │   ├── page.tsx              # Landing page
│   │   └── api/
│   │       └── proxy/            # API proxy (legacy)
│   ├── components/
│   │   └── WorkflowDemo.tsx      # Interactive demo
│   └── lib/
│       └── supabase.ts           # Supabase client & types
├── .env.local                     # Environment variables (gitignored)
├── .env.example                   # Environment template
├── vercel.json                    # Deployment config
└── README.md
```

## License

MIT

## Author

Mayank Sharma - [mayyanks.app](https://mayyanks.app)
