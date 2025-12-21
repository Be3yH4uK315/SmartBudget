import { BudgetPayload, CreateBudgetPayload } from '@features/budget/types'
import { api } from '@shared/api'

class BudgetApi {
  baseUrl = '/budget'

  async getBudgetData(): Promise<BudgetPayload> {
    const url = `${this.baseUrl}`

    const response = await api.get<BudgetPayload>(url)
    return response.data
  }

  async createBudget(payload: CreateBudgetPayload): Promise<void> {
    const url = `${this.baseUrl}`

    const response = await api.post<void>(url, { payload })
    return response.data
  }
}

export const budgetApi = new BudgetApi()
