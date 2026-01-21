import {
  EditGoalPayload,
  Goal,
  GoalsFilters,
  GoalStatus,
  GoalTransaction,
  SimplifiedGoal,
  UpdateGoalStatusPayload,
} from '@features/goals/types'
import { api } from '@shared/api'

class GoalsApi {
  baseUrl = '/goals'

  async getGoals(filters: GoalsFilters): Promise<SimplifiedGoal[]> {
    const url = `${this.baseUrl}/`

    const params: Record<string, string> = {}

    if (filters.tags.length > 0) {
      params.tags = filters.tags.join(',')
    }

    if (filters.priority.length > 0) {
      params.priority = filters.priority.join(',')
    }

    if (filters.isArchived) params.isArchived = 'True'

    const response = await api.get<SimplifiedGoal[]>(url, { params })
    return response.data
  }

  async getGoal(goalId: string): Promise<Goal> {
    const url = `${this.baseUrl}?goalId=${goalId}`

    const response = await api.get<Goal>(url)
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

  async updateGoalStatus({
    goalId,
    status,
  }: UpdateGoalStatusPayload): Promise<{ status: GoalStatus }> {
    const url = `${this.baseUrl}/${status === 'closed' ? 'restore' : 'close'}`

    const response = await api.patch<{ status: GoalStatus }>(url, goalId)
    return response.data
  }

  async updateArchivedStatus(goalId: string): Promise<{ isArchived: boolean }> {
    const url = `${this.baseUrl}/archive`

    const response = await api.patch<{ isArchived: boolean }>(url, goalId)
    return response.data
  }
}

export const goalsApi = new GoalsApi()
