/**
 * Server-side token refresh route handler
 * Uses refresh_token from httpOnly cookie to get new access_token
 */

import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

// Server-side API calls use internal Docker network
const API_BASE_URL = process.env.BACKEND_API_URL || 'http://backend:8000';

/**
 * POST /api/auth/refresh
 * Reads refresh_token from cookie, calls backend, updates access_token cookie
 */
export async function POST(request: NextRequest) {
  try {
    // Get refresh_token from cookie
    const refreshToken = request.cookies.get('refresh_token')?.value;

    if (!refreshToken) {
      return NextResponse.json(
        { detail: 'Refresh token not found' },
        { status: 401 }
      );
    }

    // Call backend refresh endpoint
    const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {
      refresh_token: refreshToken
    });

    const { access_token } = response.data;

    // Create response
    const nextResponse = NextResponse.json({ success: true }, { status: 200 });

    // Update access_token cookie (30 minutes)
    nextResponse.cookies.set('access_token', access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 30 * 60, // 30 minutes in seconds
      path: '/'
    });

    return nextResponse;
  } catch (error: any) {
    console.error('Token refresh error:', error.response?.data || error.message);
    
    // Clear cookies on refresh failure
    const response = NextResponse.json(
      { detail: 'Token refresh failed' },
      { status: 401 }
    );

    response.cookies.set('access_token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 0,
      path: '/'
    });

    response.cookies.set('refresh_token', '', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 0,
      path: '/'
    });

    return response;
  }
}

