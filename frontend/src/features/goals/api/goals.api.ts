import { api } from '@shared/api'
import { CurrentGoal, EditGoalPayload, Goal } from '../types/goals'

class GoalsApi {
  baseUrl = '/goals'

  async getGoals(): Promise<Goal[]> {
    const url = `${this.baseUrl}/main`

    const response = await api.get<Goal[]>(url)
    return response.data
  }

  async getGoal(goalId: string): Promise<CurrentGoal> {
    const url = `${this.baseUrl}?goalId=${goalId}`

    const response = await api.get<CurrentGoal>(url)
    return response.data
  }

  async editGoal(payload: EditGoalPayload): Promise<void> {
    const { goalId, ...body } = payload
    const url = `${this.baseUrl}/${goalId}`

    const response = await api.patch<void>(url, { body })
    return response.data
  }

  async createGoal(payload: Omit<EditGoalPayload, 'goalId'>): Promise<string> {
    const url = `${this.baseUrl}`

    const response = await api.post<string>(url, { payload })
    return response.data
  }
}

export const goalsApi = new GoalsApi()
