import { api } from '@shared/api'
import { User } from '@shared/types'

class User_api {
  baseURL = '/user'

  async getUserInfo(): Promise<User> {
    const url = `${this.baseURL}/me`
    const response = await api.get<User>(url)

    return response.data
  }
}

export const user_api = new User_api()
