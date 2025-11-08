type SignInAction = 'sign_in' | 'sign_up' | 'reset_password'
type VerifyMode = 'signup' | 'reset' | null
type AuthStep = 'email' | 'password' | 'verifyEmail'

type AuthResponse = {
  action: SignInAction
  details: string
  status: string
}

type VerifyEmail = {
  email: string
}

type VerifyLink = {
  token: string
  email: string
}

type CompleteRegistration = {
  email: string
  token: string
  password: string
  name: string
  country: string
  user_agent?: string
}

type Login = {
  email: string
  password: string
}

type ResetPassword = {
  email: string
}

type CompleteReset = {
  email: string
  token: string
  new_password: string
}
