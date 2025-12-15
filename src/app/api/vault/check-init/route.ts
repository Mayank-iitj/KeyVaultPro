import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { userId } = body;

    if (!userId) {
      return NextResponse.json(
        { error: 'User ID required' },
        { status: 400 }
      );
    }

    const { data: users, error } = await supabase
      .from('users')
      .select('vault_initialized')
      .eq('id', userId);

    if (error) throw error;

    if (!users || users.length === 0) {
      const { error: insertError } = await supabase
        .from('users')
        .insert({
          id: userId,
          email: `vault-user-${userId.slice(0, 8)}@temp.local`,
          username: `vault-user-${userId.slice(0, 8)}`,
          password_hash: 'temp',
          vault_initialized: false,
        });
      
      if (insertError) throw insertError;
      
      return NextResponse.json({ initialized: false });
    }

    return NextResponse.json({ initialized: users[0]?.vault_initialized || false });
  } catch (error) {
    console.error('Check init error:', error);
    return NextResponse.json(
      { error: 'Failed to check initialization status' },
      { status: 500 }
    );
  }
}