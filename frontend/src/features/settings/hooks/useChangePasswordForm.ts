import { useMemo, useState } from 'react'
import { changePassword } from '@features/settings/store/security'
import { ChangePasswordErrors, ChangePasswordFormValues } from '@features/settings/types'
import { useTranslate } from '@shared/hooks'
import { dispatch } from '@shared/store'

export function useChangePasswordFrom() {
  const translate = useTranslate('Settings.Security.ChangePassword.Errors')

  const [values, setValues] = useState<ChangePasswordFormValues>({
    password: '',
    newPassword: '',
    newPasswordConfirm: '',
  })

  const [touched, setTouched] = useState<Partial<Record<keyof ChangePasswordFormValues, boolean>>>(
    {},
  )

  const [isSubmitted, setIsSubmitted] = useState(false)

  const errors = useMemo<ChangePasswordErrors>(() => {
    const { password, newPassword, newPasswordConfirm } = values
    const newErrors: ChangePasswordErrors = {}

    if (!password) newErrors.password = ''

    if (!!password && newPassword.length < 8) {
      newErrors.newPassword = translate('tooShortPassword')
    }

    if (!!newPassword && !newPasswordConfirm) {
      newErrors.newPasswordConfirm = translate('confirmPassword')
    } else if (newPassword !== newPasswordConfirm) {
      newErrors.newPasswordConfirm = translate('passwordsNotMatch')
    }

    return newErrors
  }, [values, translate])

  const canSubmit = Object.keys(errors).length === 0

  const handleChange =
    <K extends keyof ChangePasswordFormValues>(key: K) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value

      setTouched((prev) => ({ ...prev, [key]: true }))

      setValues((prev) => ({
        ...prev,
        [key]: value,
      }))
    }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitted(true)

    if (!canSubmit) return

    dispatch(
      changePassword({
        password: values.password,
        newPassword: values.newPassword,
      }),
    )
  }

  const shouldShowError = (field: keyof ChangePasswordFormValues) =>
    !!errors[field] && (touched[field] || isSubmitted)

  return {
    values,
    errors,
    shouldShowError,
    handleChange,
    canSubmit,
    handleSubmit,
  }
}
