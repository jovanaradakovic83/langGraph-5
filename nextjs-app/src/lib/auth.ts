import jwt from 'jsonwebtoken'
import { JWTPayload, AuthError } from '@/types'

const JWT_SECRET = process.env.JWT_SECRET!
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET!

const ACCESS_TOKEN_TTL = '15m'
const REFRESH_TOKEN_TTL = '7d'

// Sign a new access token for a given user payload
export function signAccessToken(payload: Omit<JWTPayload, 'iat' | 'exp'>): string {
  return jwt.sign(payload, JWT_SECRET, { expiresIn: ACCESS_TOKEN_TTL })
}

// Sign a new refresh token
export function signRefreshToken(userId: string): string {
  return jwt.sign({ sub: userId }, JWT_REFRESH_SECRET, { expiresIn: REFRESH_TOKEN_TTL })
}

// Decode a token without verifying — useful for reading claims from an expired token
export function decodeToken(token: string): JWTPayload | null {
  try {
    return jwt.decode(token) as JWTPayload
  } catch {
    return null
  }
}

// Verify a token is valid and not expired — throws if invalid
export function verifyAccessToken(token: string): JWTPayload {
  try {
    return jwt.verify(token, JWT_SECRET) as JWTPayload
  } catch (err) {
    const authError: AuthError = {
      code: err instanceof jwt.TokenExpiredError ? 'TOKEN_EXPIRED' : 'INVALID_TOKEN',
      message: err instanceof jwt.TokenExpiredError
        ? 'Access token has expired'
        : 'Invalid access token',
    }
    throw authError
  }
}

// Verify a refresh token
export function verifyRefreshToken(token: string): { sub: string } {
  try {
    return jwt.verify(token, JWT_REFRESH_SECRET) as { sub: string }
  } catch {
    const authError: AuthError = {
      code: 'INVALID_TOKEN',
      message: 'Invalid or expired refresh token',
    }
    throw authError
  }
}

// Check if a token is within N seconds of expiring
export function isTokenExpiringSoon(token: string, bufferSeconds = 300): boolean {
  const payload = decodeToken(token)
  if (!payload?.exp) return true
  const nowSeconds = Math.floor(Date.now() / 1000)
  return payload.exp - nowSeconds < bufferSeconds
}
