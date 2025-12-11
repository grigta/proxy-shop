import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';

/**
 * Root page component
 * Redirects users based on their authentication status:
 * - Authenticated users -> /dashboard
 * - Unauthenticated users -> /login
 */
export default async function RootPage() {
  // Get access token from cookies to determine auth status
  const cookieStore = await cookies();
  const accessToken = cookieStore.get('access_token');

  // Redirect based on authentication
  if (accessToken) {
    redirect('/dashboard');
  } else {
    redirect('/login');
  }
}

