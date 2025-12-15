import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function DELETE(request: NextRequest) {
  try {
    const body = await request.json();
    const { vaultId, userId } = body;

    if (!vaultId || !userId) {
      return NextResponse.json(
        { error: 'Vault ID and User ID required' },
        { status: 400 }
      );
    }

    const { data: vault } = await supabase
      .from('api_vault')
      .select('platform_name')
      .eq('id', vaultId)
      .eq('user_id', userId)
      .single();

    const { error } = await supabase
      .from('api_vault')
      .update({ is_active: false })
      .eq('id', vaultId)
      .eq('user_id', userId);

    if (error) throw error;

    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    const userAgent = request.headers.get('user-agent') || 'unknown';

    await supabase.from('vault_audit_log').insert({
      vault_id: vaultId,
      user_id: userId,
      action: 'delete',
      ip_address: ip,
      user_agent: userAgent,
      success: true,
      metadata: { platform_name: vault?.platform_name },
    });

    return NextResponse.json({ success: true });
  } catch (error: unknown) {
    console.error('Vault delete error:', error);
    return NextResponse.json(
      { error: 'Failed to delete vault' },
      { status: 500 }
    );
  }
}