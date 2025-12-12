export type SignInAction =
  | 'sign_in'
  | 'sign_up'
  | 'reset_password'
  | 'complete_registration'
  | 'complete_reset'

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
  token_type: string
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
  new_password: string
}
