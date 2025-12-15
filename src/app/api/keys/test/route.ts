import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import bcrypt from 'bcryptjs';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: NextRequest) {
  try {
    const { keyId, apiKey, userId } = await request.json();

    if (!keyId || !apiKey || !userId) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const { data: key, error } = await supabase
      .from('api_keys')
      .select('*')
      .eq('id', keyId)
      .eq('is_active', true)
      .single();

    if (error || !key) {
      return NextResponse.json(
        { error: 'Invalid or inactive API key' },
        { status: 401 }
      );
    }

    const keyMatch = await bcrypt.compare(apiKey, key.key_hash);
    if (!keyMatch) {
      return NextResponse.json(
        { error: 'API key verification failed' },
        { status: 401 }
      );
    }

    await supabase
      .from('api_keys')
      .update({ last_used_at: new Date().toISOString() })
      .eq('id', keyId);

    await supabase.from('audit_logs').insert({
      user_id: userId,
      api_key_id: keyId,
      action: 'API_ENDPOINT_ACCESSED',
      metadata: { endpoint: '/protected/test', method: 'GET', status: 'success' },
    });

    return NextResponse.json({
      success: true,
      message: 'API key validated',
      user_id: userId,
      permissions: key.permissions,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'API key test failed' },
      { status: 500 }
    );
  }
}
