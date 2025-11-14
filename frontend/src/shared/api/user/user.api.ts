import { api } from '@shared/api'

class User_api {
  baseURL = '/user'

  async getUserInfo() {
    const url = `${this.baseURL}/get_user_info`
    const response = await api.get<User>(url)

    return response.data
  }
}

export const user_api = new User_api()
