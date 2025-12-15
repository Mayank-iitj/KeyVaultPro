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
      .select('vault_initialized')
      .eq('id', userId)
      .single();

    if (userError) throw userError;

    if (user?.vault_initialized) {
      return NextResponse.json(
        { error: 'Master password already initialized' },
        { status: 400 }
      );
    }

    const salt = crypto.randomBytes(32).toString('hex');
    const hash = hashMasterPassword(masterPassword, salt);

    const { error: updateError } = await supabase
      .from('users')
      .update({
        master_password_hash: hash,
        master_password_salt: salt,
        vault_initialized: true,
      })
      .eq('id', userId);

    if (updateError) throw updateError;

    return NextResponse.json({ success: true, message: 'Master password initialized' });
  } catch (error) {
    console.error('Master password init error:', error);
    return NextResponse.json(
      { error: 'Failed to initialize master password' },
      { status: 500 }
    );
  }
}
