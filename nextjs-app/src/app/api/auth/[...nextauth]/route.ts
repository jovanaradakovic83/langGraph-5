import { NextRequest, NextResponse } from 'next/server'
import { signAccessToken, signRefreshToken, verifyRefreshToken } from '@/lib/auth'
import { setSession, clearSession } from '@/lib/session'
import { ApiResponse, User } from '@/types'

// POST /api/auth/login
async function login(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  try {
    const { email, password } = await request.json()

    if (!email || !password) {
      return NextResponse.json({ error: 'Email and password are required', status: 400 }, { status: 400 })
    }

    // Placeholder: replace with real DB lookup + bcrypt comparison
    const user: User = {
      id: 'usr_demo_001',
      email,
      name: 'Demo User',
      role: 'user',
      createdAt: new Date(),
      updatedAt: new Date(),
    }

    const accessToken = signAccessToken({ sub: user.id, email: user.email, role: user.role })
    const refreshToken = signRefreshToken(user.id)

    await setSession(accessToken, refreshToken)

    return NextResponse.json({ data: { userId: user.id, email: user.email }, status: 200 })
  } catch (err) {
    console.error('[auth/login]', err)
    return NextResponse.json({ error: 'Internal server error', status: 500 }, { status: 500 })
  }
}

// POST /api/auth/refresh
async function refresh(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  try {
    const refreshToken = request.cookies.get('refresh_token')?.value

    if (!refreshToken) {
      return NextResponse.json({ error: 'No refresh token provided', status: 401 }, { status: 401 })
    }

    const { sub: userId } = verifyRefreshToken(refreshToken)

    // Placeholder: fetch fresh user claims from DB
    const newAccessToken = signAccessToken({ sub: userId, email: 'user@example.com', role: 'user' })
    const newRefreshToken = signRefreshToken(userId)

    await setSession(newAccessToken, newRefreshToken)

    return NextResponse.json({ data: { refreshed: true }, status: 200 })
  } catch (err) {
    console.error('[auth/refresh]', err)
    return NextResponse.json({ error: 'Could not refresh session', status: 401 }, { status: 401 })
  }
}

// POST /api/auth/logout
async function logout(): Promise<NextResponse<ApiResponse>> {
  await clearSession()
  return NextResponse.json({ data: { loggedOut: true }, status: 200 })
}

export async function POST(
  request: NextRequest,
  { params }: { params: { nextauth: string[] } }
): Promise<NextResponse<ApiResponse>> {
  const action = params.nextauth[0]

  if (action === 'login') return login(request)
  if (action === 'refresh') return refresh(request)
  if (action === 'logout') return logout()

  return NextResponse.json({ error: 'Unknown auth action', status: 404 }, { status: 404 })
}
