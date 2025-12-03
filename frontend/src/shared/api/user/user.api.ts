import { apiME } from '@shared/api'

class User_api {
  baseURL = '/user'

  async getUserInfo(): Promise<User> {
    const url = `${this.baseURL}/me`
    const response = await apiME.get<User>(url)

    return response.data
  }
}

export const user_api = new User_api()
