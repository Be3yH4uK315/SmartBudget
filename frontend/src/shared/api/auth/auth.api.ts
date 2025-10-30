import { api, req } from '@shared/api'

const getUserAgent = () => (typeof navigator !== 'undefined' ? navigator.userAgent : undefined)

class Auth_api {
  baseUrl = '/auth'

  /** Метод для определения след. шага сценария авторизации/регистрации
   * @param payload: {
   *    email: string
   * }
   * @returns name: string - пустая строка '' → новый пользователь
   *                         непустое имя → пользователь существует
   */
  async verifyEmail(payload: VerifyEmail): Promise<string> {
    const url = `${this.baseUrl}/verify-email`

    const response = await req<VerifyEmailResponse>(api.post(url, payload))
    return response.name /** '' -> регистрация, 'имя' -> логин */
  }

  /** Метод для проверки токена из письма при регистрации
   * @param params : {
   *    token: string
   *    email: string
   * }
   * @returns true при валидном токене
   */
  async verifyLink(params: VerifyLink): Promise<boolean> {
    const url = `${this.baseUrl}/verify-link`

    const response = await req<Ok>(api.get(url, { params }))
    return !!response?.ok
  }

  /** Метод для этапа регистрации
   * @param payload : {
   *    email: string
   *    token: string
   *    password: string
   *    name: string
   *    country: string
   *    user_agent: string | undefined
   * }
   * @returns true при успехе
   */
  async completeRegistration(payload: CompleteRegistration): Promise<boolean> {
    const url = `${this.baseUrl}/complete-registration`
    const body = { user_agent: getUserAgent(), ...payload }

    const response = await req<Ok>(api.post(url, body))
    return !!response?.ok
  }

  /** Метод для авторизации
   * @param payload : {
   *    email: string
   *    password: string
   *    user_agent: string | undefined
   * }
   * @returns true при успехе
   */
  async login(payload: Login): Promise<boolean> {
    const url = `${this.baseUrl}/login`
    const body = { user_agent: getUserAgent(), ...payload }

    const response = await req<Ok>(api.post(url, body))
    return !!response?.ok
  }

  /** Метод для выхода из аккаунта
   * @returns true при успехе
   */
  async logout(): Promise<boolean> {
    const url = `${this.baseUrl}/logout`

    const response = await req<Ok>(api.post(url))
    return !!response?.ok
  }

  /** Метод для сброса пароля
   * @param payload : {
   *    email: string
   * }
   * @returns
   */
  async resetPassword(payload: ResetPassword): Promise<boolean> {
    const url = `${this.baseUrl}/reset-password`

    const response = await req<Ok>(api.post(url, payload))
    return !!response?.ok
  }

  /**
   *
   * @param payload : {
   *    email: string
   *    token: string
   *    new_password: string
   * }
   * @returns
   */
  async completeReset(payload: CompleteReset): Promise<boolean> {
    const url = `${this.baseUrl}/complete-reset`

    const response = await req<Ok>(api.post(url, payload))
    return !!response?.ok
  }

  /** Метод для рефреша токена */
  async refresh(): Promise<boolean> {
    const url = `${this.baseUrl}/refresh`

    const response = await req<Ok>(api.post(url, {}))
    return !!response?.ok
  }

  /** Метод для валидации токена
   * @param token : string
   * @returns true при успехе
   */
  async validateToken(token: string): Promise<boolean> {
    const url = `${this.baseUrl}/validate-token`

    const response = await req<Ok>(api.post(url, { token }))
    return !!response?.ok
  }
}

export const auth_api = new Auth_api()
