import { NextRequest, NextResponse } from 'next/server'
import { verifyAccessToken } from '@/lib/auth'
import { AuthError } from '@/types'

// Routes that do not require authentication
const PUBLIC_PATHS = ['/login', '/register', '/api/auth']

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl

  // Allow public routes through without token check
  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    return NextResponse.next()
  }

  const accessToken = request.cookies.get('access_token')?.value

  if (!accessToken) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  try {
    // Verify token is valid — but does NOT check if it is close to expiry.
    // Auto-refresh of expiring tokens is not yet implemented here.
    const payload = verifyAccessToken(accessToken)

    // Forward user identity to downstream route handlers via headers
    const requestHeaders = new Headers(request.headers)
    requestHeaders.set('x-user-id', payload.sub)
    requestHeaders.set('x-user-role', payload.role)

    return NextResponse.next({ request: { headers: requestHeaders } })
  } catch (err) {
    const authError = err as AuthError

    // Expired tokens redirect to login; other invalid tokens get a 401
    if (authError.code === 'TOKEN_EXPIRED') {
      // TODO: attempt silent refresh before redirecting — not yet implemented
      return NextResponse.redirect(new URL('/login', request.url))
    }

    return NextResponse.json({ error: authError.message, status: 401 }, { status: 401 })
  }
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
