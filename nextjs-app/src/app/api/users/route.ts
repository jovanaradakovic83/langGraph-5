import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { ApiResponse, User } from '@/types'

// GET /api/users/me — returns the current authenticated user's profile
export async function GET(request: NextRequest): Promise<NextResponse<ApiResponse<User>>> {
  try {
    const session = await getSession()

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized', status: 401 }, { status: 401 })
    }

    // Placeholder: replace with real DB lookup by session.userId
    const user: User = {
      id: session.userId,
      email: session.email,
      name: 'Demo User',
      role: session.role,
      createdAt: new Date(),
      updatedAt: new Date(),
    }

    return NextResponse.json({ data: user, status: 200 })
  } catch (err) {
    console.error('[GET /api/users]', err)
    return NextResponse.json({ error: 'Internal server error', status: 500 }, { status: 500 })
  }
}

// PATCH /api/users/me — updates the current user's profile
export async function PATCH(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  try {
    const session = await getSession()

    if (!session) {
      return NextResponse.json({ error: 'Unauthorized', status: 401 }, { status: 401 })
    }

    const body = await request.json()

    if (!body || typeof body !== 'object') {
      return NextResponse.json({ error: 'Invalid request body', status: 400 }, { status: 400 })
    }

    const allowedFields = ['name']
    const update = Object.fromEntries(
      Object.entries(body).filter(([key]) => allowedFields.includes(key))
    )

    // Placeholder: replace with real DB update
    return NextResponse.json({ data: { updated: true, fields: Object.keys(update) }, status: 200 })
  } catch (err) {
    console.error('[PATCH /api/users]', err)
    return NextResponse.json({ error: 'Internal server error', status: 500 }, { status: 500 })
  }
}
