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

  const resetForm = () => {
    setValues({ password: '', newPassword: '', newPasswordConfirm: '' })
    setTouched({})
  }

  const handleBlur =
    <K extends keyof ChangePasswordFormValues>(key: K) =>
    () => {
      setTouched((prev) => ({ ...prev, [key]: true }))
    }

  const handleChange =
    <K extends keyof ChangePasswordFormValues>(key: K) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value

      setValues((prev) => ({ ...prev, [key]: value }))
    }

  const errors = (): ChangePasswordErrors => {
    const { password, newPassword, newPasswordConfirm } = values
    const newErrors: ChangePasswordErrors = {}

    if (!password) newErrors.password = ''

    if (touched.newPassword && newPassword.length < 8) {
      newErrors.newPassword = translate('tooShortPassword')
    }

    if (
      touched.newPasswordConfirm &&
      newPasswordConfirm.length > 0 &&
      newPassword !== newPasswordConfirm
    ) {
      newErrors.newPasswordConfirm = translate('passwordsNotMatch')
    }

    return newErrors
  }

  const canSubmit = () => Object.keys(errors()).length === 0

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setTouched({
      password: true,
      newPassword: true,
      newPasswordConfirm: true,
    })

    if (!canSubmit()) {
      showToast({ messageKey: 'cannotSubmitForm', type: 'error' })
      return
    }

    try {
      await dispatch(
        changePassword({
          password: values.password,
          newPassword: values.newPassword,
        }),
      ).unwrap()

      resetForm()
    } catch {}
  }

  const shouldShowError = (field: keyof ChangePasswordFormValues) =>
    touched[field] && !!errors()[field]

  return {
    values,
    errors,
    shouldShowError,
    handleChange,
    handleSubmit,
    handleBlur,
  }
}
