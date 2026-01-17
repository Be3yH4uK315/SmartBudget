export type Session = {
  sessionId: string
  isCurrent: boolean
  ip: string
  location: string
  deviceName: string
  lastActivity: string
}

export type changePasswordApiRequest = {
  password: string
  newPassword: string
}

export type ChangePasswordFormValues = {
  password: string
  newPassword: string
  newPasswordConfirm: string
}

export type ChangePasswordErrors = Partial<Record<keyof ChangePasswordFormValues, string>>

export type RefreshTokenFormItem = {
  label: string
  value: number
}
