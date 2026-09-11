// Core domain types shared across the application

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'user' | 'guest'
  createdAt: Date
  updatedAt: Date
}

export interface Session {
  userId: string
  email: string
  role: User['role']
  accessToken: string
  refreshToken: string
  // NOTE: expiry tracking not yet implemented — see lib/session.ts
}

export interface JWTPayload {
  sub: string       // user id
  email: string
  role: User['role']
  iat: number       // issued at (unix timestamp)
  exp: number       // expiry (unix timestamp)
}

export interface ApiResponse<T = unknown> {
  data?: T
  error?: string
  status: number
}

export interface AuthError {
  code: 'UNAUTHORIZED' | 'FORBIDDEN' | 'TOKEN_EXPIRED' | 'INVALID_TOKEN'
  message: string
}
