import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import bcrypt from 'bcryptjs';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: NextRequest) {
  try {
    const { userId, name, apiKey, pin, permissions } = await request.json();

    if (!userId || !name || !apiKey || !pin) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const keyHash = await bcrypt.hash(apiKey, 10);
    const pinHash = await bcrypt.hash(pin, 10);

    const { data, error } = await supabase
      .from('api_keys')
      .insert({
        user_id: userId,
        name,
        key_hash: keyHash,
        key_preview: apiKey.substring(0, 12) + '...',
        permissions: permissions || ['read', 'write'],
        pin_hash: pinHash,
        is_active: true,
        expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      })
      .select()
      .single();

    if (error) {
      return NextResponse.json(
        { error: error.message },
        { status: 400 }
      );
    }

    await supabase.from('audit_logs').insert({
      user_id: userId,
      api_key_id: data.id,
      action: 'API_KEY_CREATED',
      metadata: { key_name: name, permissions: data.permissions },
    });

    return NextResponse.json({
      id: data.id,
      name: data.name,
      preview: data.key_preview,
      permissions: data.permissions,
      expires_at: data.expires_at,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Key creation failed' },
      { status: 500 }
    );
  }
}
