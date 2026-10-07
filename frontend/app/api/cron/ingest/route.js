import { NextResponse } from 'next/server';

export async function GET(request) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  try {
    const res = await fetch(`${backendUrl}/api/market/ingest-cycle`, {
      method: 'POST',
      cache: 'no-store',
      headers: {
        'Cache-Control': 'no-cache',
      },
    });
    const data = await res.json().catch(() => ({}));
    return NextResponse.json({ success: true, trigger: data });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}
