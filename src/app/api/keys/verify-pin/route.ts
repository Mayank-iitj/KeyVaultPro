import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';
import bcrypt from 'bcryptjs';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

export async function POST(request: NextRequest) {
  try {
    const { keyId, pin, userId } = await request.json();

    if (!keyId || !pin || !userId) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const { data: key, error } = await supabase
      .from('api_keys')
      .select('pin_hash')
      .eq('id', keyId)
      .single();

    if (error || !key) {
      return NextResponse.json(
        { error: 'API key not found' },
        { status: 404 }
      );
    }

    const pinMatch = await bcrypt.compare(pin, key.pin_hash);
    if (!pinMatch) {
      return NextResponse.json(
        { error: 'Invalid PIN' },
        { status: 401 }
      );
    }

    await supabase.from('audit_logs').insert({
      user_id: userId,
      api_key_id: keyId,
      action: 'API_KEY_VIEWED',
      metadata: { verification: 'PIN_VERIFIED' },
    });

    return NextResponse.json({
      pin_verified: true,
      message: 'PIN verified successfully',
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'PIN verification failed' },
      { status: 500 }
    );
  }
}
