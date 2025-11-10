import { api } from '@shared/api'

const getUserAgent = () => (typeof navigator !== 'undefined' ? navigator.userAgent : undefined)

class AuthApi {
  baseUrl = '/auth'

  async verifyEmail(payload: VerifyEmail): Promise<AuthResponse> {
    const url = `${this.baseUrl}/verify-email`

    const response = await api.post<AuthResponse>(url, payload)
    return response.data
  }

  async verifyLink(params: VerifyLink): Promise<AuthResponse> {
    const url = `${this.baseUrl}/verify-link`

    const response = await api.get<AuthResponse>(url, { params })
    return response.data
  }

  async completeRegistration(payload: CompleteRegistration): Promise<AuthResponse> {
    const url = `${this.baseUrl}/complete-registration`
    const body = { user_agent: getUserAgent(), ...payload }

    const response = await api.post<AuthResponse>(url, body)
    return response.data
  }

  async login(payload: Login): Promise<AuthResponse> {
    const url = `${this.baseUrl}/login`
    const body = { user_agent: getUserAgent(), ...payload }

    const response = await api.post<AuthResponse>(url, body)
    return response.data
  }

  async logout(): Promise<AuthResponse> {
    const url = `${this.baseUrl}/logout`

    const response = await api.post<AuthResponse>(url)
    return response.data
  }

  async resetPassword(payload: ResetPassword): Promise<AuthResponse> {
    const url = `${this.baseUrl}/reset-password`

    const response = await api.post<AuthResponse>(url, payload)
    return response.data
  }

  async completeReset(payload: CompleteReset): Promise<AuthResponse> {
    const url = `${this.baseUrl}/complete-reset`

    const response = await api.post<AuthResponse>(url, payload)
    return response.data
  }

  async refresh(): Promise<boolean> {
    const url = `${this.baseUrl}/refresh`

    const response = await api.post<any>(url, {})
    return response.data
  }

  async validateToken(token: string): Promise<boolean> {
    const url = `${this.baseUrl}/validate-token`

    const response = await api.post<any>(url, { token })
    return response.data
  }
}

export const authApi = new AuthApi()
