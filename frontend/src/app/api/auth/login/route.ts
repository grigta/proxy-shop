/**
 * Server-side login route handler
 * Proxies login request to backend and sets httpOnly cookies
 */

import { NextRequest, NextResponse } from 'next/server';
import axios from 'axios';

// Server-side API calls use internal Docker network
const API_BASE_URL = process.env.BACKEND_API_URL || 'http://backend:8000';

/**
 * POST /api/auth/login
 * Receives access_code, calls backend, sets httpOnly cookies
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { access_code } = body;

    if (!access_code) {
      return NextResponse.json(
        { detail: 'Access code is required' },
        { status: 400 }
      );
    }

    // Call backend login endpoint
    const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
      access_code
    });

    const { access_token, refresh_token, ...userData } = response.data;

    // Create response with user data (without tokens in body)
    const nextResponse = NextResponse.json(userData, { status: 200 });

    // Set httpOnly cookies for tokens
    // Access token: 30 minutes
    nextResponse.cookies.set('access_token', access_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 30 * 60, // 30 minutes in seconds
      path: '/'
    });

    // Refresh token: 7 days
    nextResponse.cookies.set('refresh_token', refresh_token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60, // 7 days in seconds
      path: '/'
    });

    return nextResponse;
  } catch (error: any) {
    console.error('Login error:', error.response?.data || error.message);
    
    return NextResponse.json(
      {
        detail: error.response?.data?.detail || 'Login failed'
      },
      { status: error.response?.status || 500 }
    );
  }
}

