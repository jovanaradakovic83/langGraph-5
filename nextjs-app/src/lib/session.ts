import { cookies } from 'next/headers'
import { Session, JWTPayload } from '@/types'
import { verifyAccessToken, decodeToken } from '@/lib/auth'

const ACCESS_COOKIE = 'access_token'
const REFRESH_COOKIE = 'refresh_token'

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  path: '/',
}

// Retrieve the current session from cookies.
// Returns null if no token is present or the token is invalid.
// NOTE: Does NOT handle token expiry or auto-refresh — this needs to be added.
export async function getSession(): Promise<Session | null> {
  const cookieStore = await cookies()
  const accessToken = cookieStore.get(ACCESS_COOKIE)?.value

  if (!accessToken) return null

  try {
    const payload: JWTPayload = verifyAccessToken(accessToken)
    return {
      userId: payload.sub,
      email: payload.email,
      role: payload.role,
      accessToken,
      refreshToken: cookieStore.get(REFRESH_COOKIE)?.value ?? '',
    }
  } catch {
    // Token invalid or expired — caller must handle
    return null
  }
}

// Persist session tokens as HTTP-only cookies
export async function setSession(accessToken: string, refreshToken: string): Promise<void> {
  const cookieStore = await cookies()
  const payload = decodeToken(accessToken)

  cookieStore.set(ACCESS_COOKIE, accessToken, {
    ...COOKIE_OPTIONS,
    maxAge: payload?.exp ? payload.exp - Math.floor(Date.now() / 1000) : 900,
  })

  cookieStore.set(REFRESH_COOKIE, refreshToken, {
    ...COOKIE_OPTIONS,
    maxAge: 60 * 60 * 24 * 7, // 7 days
  })
}

// Clear all session cookies (logout)
export async function clearSession(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(ACCESS_COOKIE)
  cookieStore.delete(REFRESH_COOKIE)
}

// TODO: refreshSession() — use the refresh token to obtain a new access token
// and update the cookies without interrupting the user's request.
// This is not yet implemented.
