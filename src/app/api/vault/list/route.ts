import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function GET(request: NextRequest) {
  try {
    const userId = request.nextUrl.searchParams.get('userId');

    if (!userId) {
      return NextResponse.json({ error: 'User ID required' }, { status: 400 });
    }

    const { data, error } = await supabase
      .from('api_vault')
      .select('*')
      .eq('user_id', userId)
      .eq('is_active', true)
      .order('created_at', { ascending: false });

    if (error) throw error;

    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    const userAgent = request.headers.get('user-agent') || 'unknown';

    await supabase.from('vault_audit_log').insert({
      user_id: userId,
      action: 'list',
      ip_address: ip,
      user_agent: userAgent,
    });

    return NextResponse.json({ success: true, vaults: data });
  } catch (error: unknown) {
    console.error('Vault list error:', error);
    return NextResponse.json(
      { error: 'Failed to retrieve vaults' },
      { status: 500 }
    );
  }
}
