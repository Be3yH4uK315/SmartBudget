export type Session = {
  sessionId: string
  isCurrentSession: boolean
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
  password: ''
  newPassword: ''
  newPasswordConfirm: ''
}

export type ChangePasswordErrors = Partial<Record<keyof ChangePasswordFormValues, string>>
