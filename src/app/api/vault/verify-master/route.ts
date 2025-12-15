import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import * as crypto from 'crypto';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

function hashMasterPassword(password: string, salt: string): string {
  return crypto.pbkdf2Sync(password, salt, 600000, 64, 'sha512').toString('hex');
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { userId, masterPassword } = body;

    if (!userId || !masterPassword) {
      return NextResponse.json(
        { error: 'User ID and master password required' },
        { status: 400 }
      );
    }

    const { data: user, error: userError } = await supabase
      .from('users')
      .select('master_password_hash, master_password_salt, vault_initialized')
      .eq('id', userId)
      .single();

    if (userError) throw userError;

    if (!user?.vault_initialized) {
      return NextResponse.json({ initialized: false });
    }

    const hash = hashMasterPassword(masterPassword, user.master_password_salt);
    const valid = hash === user.master_password_hash;

    return NextResponse.json({ valid, initialized: true });
  } catch (error) {
    console.error('Master password verify error:', error);
    return NextResponse.json(
      { error: 'Failed to verify master password' },
      { status: 500 }
    );
  }
}
