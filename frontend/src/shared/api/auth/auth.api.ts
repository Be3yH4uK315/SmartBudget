import { api, req } from '@shared/api'

const getUserAgent = () => (typeof navigator !== 'undefined' ? navigator.userAgent : undefined)

class Auth_api {
  baseUrl = '/auth'

  async verifyEmail(payload: VerifyEmail): Promise<string> {
    const url = `${this.baseUrl}/verify-email`

    const response = await req<VerifyEmailResponse>(api.post(url, payload))
    return response.action
  }

  async verifyLink(params: VerifyLink): Promise<boolean> {
    const url = `${this.baseUrl}/verify-link`

    const response = await req<Ok>(api.get(url, { params }))
    return !!response?.ok
  }

  async completeRegistration(payload: CompleteRegistration): Promise<boolean> {
    const url = `${this.baseUrl}/complete-registration`
    const body = { user_agent: getUserAgent(), ...payload }

    const response = await req<Ok>(api.post(url, body))
    return !!response?.ok
  }

  async login(payload: Login): Promise<boolean> {
    const url = `${this.baseUrl}/login`
    const body = { user_agent: getUserAgent(), ...payload }

    const response = await req<Ok>(api.post(url, body))
    return !!response?.ok
  }

  async logout(): Promise<boolean> {
    const url = `${this.baseUrl}/logout`

    const response = await req<Ok>(api.post(url))
    return !!response?.ok
  }

  async resetPassword(payload: ResetPassword): Promise<boolean> {
    const url = `${this.baseUrl}/reset-password`

    const response = await req<Ok>(api.post(url, payload))
    return !!response?.ok
  }

  async completeReset(payload: CompleteReset): Promise<boolean> {
    const url = `${this.baseUrl}/complete-reset`

    const response = await req<Ok>(api.post(url, payload))
    return !!response?.ok
  }

  async refresh(): Promise<boolean> {
    const url = `${this.baseUrl}/refresh`

    const response = await req<Ok>(api.post(url, {}))
    return !!response?.ok
  }

  async validateToken(token: string): Promise<boolean> {
    const url = `${this.baseUrl}/validate-token`

    const response = await req<Ok>(api.post(url, { token }))
    return !!response?.ok
  }
}

export const auth_api = new Auth_api()
