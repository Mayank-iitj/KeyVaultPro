import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { vaultId, userId } = body;

    if (!vaultId || !userId) {
      return NextResponse.json(
        { error: 'Vault ID and User ID required' },
        { status: 400 }
      );
    }

    const { data, error } = await supabase
      .from('api_vault')
      .select('*')
      .eq('id', vaultId)
      .eq('user_id', userId)
      .eq('is_active', true)
      .single();

    if (error || !data) {
      return NextResponse.json({ error: 'Vault not found' }, { status: 404 });
    }

    await supabase
      .from('api_vault')
      .update({ last_accessed_at: new Date().toISOString() })
      .eq('id', vaultId);

    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    const userAgent = request.headers.get('user-agent') || 'unknown';

    await supabase.from('vault_audit_log').insert({
      vault_id: vaultId,
      user_id: userId,
      action: 'retrieve',
      ip_address: ip,
      user_agent: userAgent,
      metadata: { platform_name: data.platform_name },
    });

    return NextResponse.json({ success: true, vault: data });
  } catch (error: unknown) {
    console.error('Vault retrieve error:', error);
    return NextResponse.json(
      { error: 'Failed to retrieve vault' },
      { status: 500 }
    );
  }
}
