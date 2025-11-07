import { useCallback,useEffect, useState } from 'react'
import { auth_mock } from '@shared/api/auth'
import { useNavigate, useSearchParams } from 'react-router'

export const useVerifyLinkFlow = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const email = (searchParams.get('email') || '').trim().toLowerCase()
  const token = (searchParams.get('token') || '').trim()

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
        const ok = await auth_mock.verifyLink({ email, token })
        if (!cancelled) setVerified(!!ok)
      } catch {
        if (!cancelled) setVerified(false)
      } finally {
        if (!cancelled) setIsVerifying(false)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [email, token])

  const wrapSubmit = useCallback(
    async (fn: () => Promise<boolean>) => {
      setIsSubmitting(true)
      try {
        const ok = await fn()
        if (ok) navigate('/main')
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
