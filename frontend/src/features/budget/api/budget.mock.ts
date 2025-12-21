import { BudgetPayload } from '@features/budget/types'

class BudgetMock {
  async getBudgetData(): Promise<BudgetPayload> {
    return Promise.resolve({
      totalLimit: 0,
      currentValue: 0,
      isAutoRenew: true,
      categories: []
    })
  }
}

export const budgetMock = new BudgetMock()
