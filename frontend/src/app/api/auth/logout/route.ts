/**
 * Server-side logout route handler
 * Clears httpOnly cookies
 */

import { NextRequest, NextResponse } from 'next/server';

/**
 * POST /api/auth/logout
 * Clears authentication cookies
 */
export async function POST(request: NextRequest) {
  const response = NextResponse.json({ success: true }, { status: 200 });

  // Clear access_token cookie
  response.cookies.set('access_token', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 0,
    path: '/'
  });

  // Clear refresh_token cookie
  response.cookies.set('refresh_token', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 0,
    path: '/'
  });

  return response;
}

