import { api } from '@shared/api'

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

    const response = await api.post<AuthResponse>(url, payload)
    return response.data
  }

  async login(payload: Login): Promise<AuthResponse> {
    const url = `${this.baseUrl}/login`

    const response = await api.post<AuthResponse>(url, payload)
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

  async refresh() {
    const url = `${this.baseUrl}/refresh`

    const response = await api.post(url)
    return response.status
  }
}

export const authApi = new AuthApi()
