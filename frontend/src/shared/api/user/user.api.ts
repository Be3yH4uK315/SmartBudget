import { api } from '@shared/api'

class User_api {
  /** времменый роут на auth для тестов */
  baseURL = '/auth'

  async getUserInfo(): Promise<User> {
    const url = `${this.baseURL}/me`
    const response = await api.get<User>(url)

    return response.data
  }
}

export const user_api = new User_api()
