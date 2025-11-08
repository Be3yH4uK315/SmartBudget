import { useCallback, useMemo, useState } from 'react'
import { auth_mock } from '@shared/api/auth'
import { useNavigate } from 'react-router'

type ErrorCode = 403 | 429 | null

export function useAuthFlow() {
  const navigate = useNavigate()

  const [step, setStep] = useState<AuthStep>('email')
  const [history, setHistory] = useState<AuthStep[]>(['email'])

  const pushStep = useCallback((next: AuthStep) => {
    setStep(next)
    setHistory((h) => [...h, next])
  }, [])

  const goBack = useCallback(() => {
    setHistory((h) => {
      if (h.length <= 1) return h
      const nextHist = h.slice(0, -1)
      setStep(nextHist[nextHist.length - 1])
      return nextHist
    })
  }, [])

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [errorCode, setErrorCode] = useState<ErrorCode>(null)
  const [isBanned, setIsBanned] = useState(false)
  const [verifyMode, setVerifyMode] = useState<VerifyMode>(null)
  const [isResending, setIsResending] = useState(false)

  const normalizedEmail = email.trim().toLowerCase()

  const canSubmit = useMemo(() => {
    if (isLoading) return false
    if (step === 'email') return /\S+@\S+\.\S+/.test(normalizedEmail)
    if (step === 'password') return password.trim().length > 0 && !isBanned
    return false
  }, [isLoading, step, normalizedEmail, password, isBanned])

  const submit = useCallback(async () => {
    if (step === 'email') {
      setIsLoading(true)
      setErrorCode(null)
      try {
        const res = await auth_api.verifyEmail({ email: normalizedEmail })
        if (res.action === 'sign_in') {
          pushStep('password')
        } else if (res.action === 'sign_up') {
          setVerifyMode('signup')
          pushStep('verifyEmail')
        } else if (res.action === 'reset_password') {
          setVerifyMode('reset')
          pushStep('verifyEmail')
        }
      } finally {
        setIsLoading(false)
      }
      return
    }

    if (step === 'password') {
      setIsLoading(true)
      setErrorCode(null)
      try {
        const res = await auth_api.login({ email: normalizedEmail, password })
        if (res) {
          navigate('/main')
          return
        }
      } catch (e: any) {
        const code = Number(e?.status || e?.code)
        if (code === 403) {
          setErrorCode(403)
        } else if (code === 429) {
          setErrorCode(429)
          setIsBanned(true)
        }
      } finally {
        setIsLoading(false)
      }
      return
    }
  }, [step, normalizedEmail, password, navigate, pushStep])

  const onKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && canSubmit) {
        e.preventDefault()
        submit()
      }
    },
    [canSubmit, submit],
  )

  const resetPasswordFlow = useCallback(() => {
    setIsLoading(true)
    setErrorCode(null)
    auth_mock
      .resetPassword({ email: normalizedEmail })
      .then((res) => {
        if (res.status === 'success') {
          setVerifyMode('reset')
          pushStep('verifyEmail')
        }
      })
      .finally(() => setIsLoading(false))
  }, [normalizedEmail, pushStep])

  const resendVerifyEmail = useCallback(async () => {
    setIsResending(true)
    try {
      const res = await auth_api.verifyEmail({ email: normalizedEmail })
      if (res.action === 'sign_up') setVerifyMode('signup')
      if (res.action === 'reset_password') setVerifyMode('reset')
    } finally {
      setIsResending(false)
    }
  }, [normalizedEmail])

  const clearBan = useCallback(() => {
    setIsBanned(false)
    setErrorCode(null)
  }, [])

  return {
    step,
    email,
    password,
    isLoading,
    canSubmit,
    normalizedEmail,
    errorCode,
    isBanned,
    verifyMode,
    isResending,

    setEmail,
    setPassword,
    submit,
    onKeyDown,
    resetPasswordFlow,
    resendVerifyEmail,
    clearBan,
    goBack,
  }
}