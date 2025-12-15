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

    const { data: user, error } = await supabase
      .from('users')
      .select('vault_initialized')
      .eq('id', userId)
      .single();

    if (error) throw error;

    return NextResponse.json({ initialized: user?.vault_initialized || false });
  } catch (error) {
    console.error('Check init error:', error);
    return NextResponse.json(
      { error: 'Failed to check initialization status' },
      { status: 500 }
    );
  }
}
