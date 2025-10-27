import { api } from '../axios.config'

class User_api {
  baseURL = ''

  async getUserInfo() {
    const url = `${this.baseURL}/get_user_info`
    const response = await api.get<User>(url)

    return response.data
  }
}

export const user_api = new User_api()
