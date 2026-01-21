import { useState } from 'react'
import { changePassword } from '@features/settings/store/security'
import { ChangePasswordErrors, ChangePasswordFormValues } from '@features/settings/types'
import { useTranslate } from '@shared/hooks'
import { dispatch } from '@shared/store'
import { showToast } from '@shared/utils'

export function useChangePasswordForm() {
  const translate = useTranslate('Settings.Security.ChangePassword.Errors')

  const [values, setValues] = useState<ChangePasswordFormValues>({
    password: '',
    newPassword: '',
    newPasswordConfirm: '',
  })

  const [touched, setTouched] = useState<Partial<Record<keyof ChangePasswordFormValues, boolean>>>(
    {},
  )

  const handleChange =
    <K extends keyof ChangePasswordFormValues>(key: K) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value
      setTouched((prev) => ({ ...prev, [key]: true }))

      setValues((prev) => ({ ...prev, [key]: value }))
    }

  const errors = (): ChangePasswordErrors => {
    const { password, newPassword, newPasswordConfirm } = values
    const newErrors: ChangePasswordErrors = {}

    if (!password) newErrors.password = ''

    if (touched.newPassword && !!newPasswordConfirm && newPassword.length < 8) {
      newErrors.newPassword = translate('tooShortPassword')
    }

    if (
      touched.newPasswordConfirm &&
      !!newPassword &&
      newPasswordConfirm.length > 0 &&
      newPassword !== newPasswordConfirm
    ) {
      newErrors.newPasswordConfirm = translate('passwordsNotMatch')
    }

    return newErrors
  }

  const canSubmit = () => Object.keys(errors()).length === 0

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!canSubmit()) {
      showToast({ messageKey: 'cannotSubmitForm', type: 'error' })
      return
    }

    dispatch(
      changePassword({
        password: values.password,
        newPassword: values.newPassword,
      }),
    )
  }

  const shouldShowError = (field: keyof ChangePasswordFormValues) => !!errors()[field]

  return {
    values,
    errors,
    shouldShowError,
    handleChange,
    handleSubmit,
  }
}
