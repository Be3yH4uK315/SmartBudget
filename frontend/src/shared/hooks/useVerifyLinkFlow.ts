import { useCallback, useEffect, useState } from 'react'
import { authApi } from '@shared/api/auth'
import { AuthResponse, TokenType } from '@shared/types'
import { useLocation, useNavigate, useSearchParams } from 'react-router'

export const useVerifyLinkFlow = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const location = useLocation()

  const email = (searchParams.get('email') || '').trim().toLowerCase()
  const token = (searchParams.get('token') || '').trim()

  const token_type: TokenType = location.pathname.includes('reset-password')
    ? 'reset'
    : 'verification'

  const [isVerifying, setIsVerifying] = useState(true)
  const [verified, setVerified] = useState<boolean | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false

    if (!email || !token) {
      setVerified(false)
      setIsVerifying(false)
      return
    }

    ;(async () => {
      setIsVerifying(true)
      try {
        const res = await authApi.verifyLink({ email, token, token_type })
        if (!cancelled) setVerified(res.status === 'success')
      } catch {
        if (!cancelled) setVerified(false)
      } finally {
        if (!cancelled) setIsVerifying(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [email, token, token_type])

  const wrapSubmit = useCallback(
    async (fn: () => Promise<AuthResponse>) => {
      setIsSubmitting(true)
      try {
        const res = await fn()
        if (res.status === 'success' && res.action === 'complete_registration') {
          navigate('/main')
          return
        }
        if (res.status === 'success' && res.action === 'complete_reset') {
          navigate('/auth/sign-in')
          return
        }
      } finally {
        setIsSubmitting(false)
      }
    },
    [navigate],
  )

  return {
    email,
    token,
    isVerifying,
    verified,
    isSubmitting,
    wrapSubmit,
  }
}
