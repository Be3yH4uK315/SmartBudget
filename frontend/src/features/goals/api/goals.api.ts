import { api } from '@shared/api'
import { CurrentGoal, EditGoalPayload, Goal, GoalTransaction } from '../types/goals'

class GoalsApi {
  baseUrl = '/goals'

  async getGoals(): Promise<Goal[]> {
    const url = `${this.baseUrl}/`

    const response = await api.get<Goal[]>(url)
    return response.data
  }

  async getGoal(goalId: string): Promise<CurrentGoal> {
    const url = `${this.baseUrl}?goalId=${goalId}`

    const response = await api.get<CurrentGoal>(url)
    return response.data
  }

  async getGoalTransactions(goalId: string): Promise<GoalTransaction[]> {
    const url = `${this.baseUrl}/transactions/${goalId}`

    const response = await api.get<GoalTransaction[]>(url)
    return response.data
  }

  async editGoal(payload: EditGoalPayload): Promise<void> {
    const { goalId, ...body } = payload
    const url = `${this.baseUrl}/${goalId}`

    const response = await api.patch<void>(url, body)
    return response.data
  }

  async createGoal(payload: Omit<EditGoalPayload, 'goalId'>): Promise<{ goalId: string }> {
    const url = `${this.baseUrl}`

    const response = await api.post<{ goalId: string }>(url, payload)
    return response.data
  }
}

export const goalsApi = new GoalsApi()
