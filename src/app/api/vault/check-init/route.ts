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

    // DEMO MODE: Reset vault on every visit
    // Delete all vault items for this user
    await supabase
      .from('vault_items')
      .delete()
      .eq('user_id', userId);

    // Check if user exists
    const { data: users } = await supabase
      .from('users')
      .select('id')
      .eq('id', userId);

    if (!users || users.length === 0) {
      // Create new user
      await supabase
        .from('users')
        .insert({
          id: userId,
          email: `vault-user-${userId.slice(0, 8)}@temp.local`,
          username: `vault-user-${userId.slice(0, 8)}`,
          password_hash: 'temp',
          vault_initialized: false,
          master_password_hash: null,
        });
    } else {
      // Reset existing user's vault
      await supabase
        .from('users')
        .update({
          vault_initialized: false,
          master_password_hash: null,
        })
        .eq('id', userId);
    }

    // Always return not initialized to force password creation
    return NextResponse.json({ 
      initialized: false,
      demoMode: true 
    });
  } catch (error) {
    console.error('Check init error:', error);
    return NextResponse.json(
      { error: 'Failed to check initialization status' },
      { status: 500 }
    );
  }
}