import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      userId,
      platformName,
      accountIdentifier,
      encryptedApiKey,
      encryptedApiSecret,
      encryptedAdditionalData,
      encryptionIv,
      encryptionSalt,
      keyType,
      environment,
      tags,
      expiresAt,
    } = body;

    if (!userId || !platformName || !encryptedApiKey || !encryptionIv || !encryptionSalt) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const { data, error } = await supabase
      .from('api_vault')
      .insert({
        user_id: userId,
        platform_name: platformName,
        account_identifier: accountIdentifier,
        encrypted_api_key: encryptedApiKey,
        encrypted_api_secret: encryptedApiSecret,
        encrypted_additional_data: encryptedAdditionalData,
        encryption_iv: encryptionIv,
        encryption_salt: encryptionSalt,
        key_type: keyType || 'api_key',
        environment: environment || 'production',
        tags: tags || [],
        expires_at: expiresAt,
      })
      .select()
      .single();

    if (error) throw error;

    const ip = request.headers.get('x-forwarded-for') || 'unknown';
    const userAgent = request.headers.get('user-agent') || 'unknown';

    await supabase.from('vault_audit_log').insert({
      vault_id: data.id,
      user_id: userId,
      action: 'store',
      ip_address: ip,
      user_agent: userAgent,
      metadata: { platform_name: platformName, key_type: keyType },
    });

    return NextResponse.json({ success: true, vaultId: data.id });
  } catch (error: unknown) {
    console.error('Vault store error:', error);
    return NextResponse.json(
      { error: 'Failed to store encrypted API key' },
      { status: 500 }
    );
  }
}
