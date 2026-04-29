export type SignInAction =
  | 'sign_in'
  | 'sign_up'
  | 'resetPassword'
  | 'completeRegistration'
  | 'completeReset'
  | 'login'

export type VerifyMode = 'signup' | 'reset' | null

export type AuthStep = 'email' | 'password' | 'verifyEmail'

export type TokenType = 'verification' | 'reset'

export type ErrorCode = 401 | 429 | null

export type AuthResponse = {
  action: SignInAction
  details: string
  status: string
}

export type VerifyEmail = {
  email: string
}

export type VerifyLink = {
  token: string
  email: string
  tokenType: string
}

export type CompleteRegistration = {
  email: string
  token: string
  password: string
  name: string
  country: string
}

export type Login = {
  email: string
  password: string
}

export type ResetPassword = {
  email: string
}

export type CompleteReset = {
  email: string
  token: string
  newPassword: string
}
