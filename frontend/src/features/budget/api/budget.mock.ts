import { BudgetPayload } from '@features/budget/types'

class BudgetMock {
  async getBudgetData(): Promise<BudgetPayload> {
    return Promise.resolve({
      totalLimit: 12000,
      currentValue: 26000,
      isAutoRenew: true,
      categories: [
        {
          categoryId: 1,
          limit: 0,
          currentValue: 2000,
        },
        {
          categoryId: 2,
          limit: 2000,
          currentValue: 2000,
        },
        {
          categoryId: 4,
          limit: 2001,
          currentValue: 2000,
        },
        {
          categoryId: 5,
          limit: 0,
          currentValue: 20000,
        },
        {
          categoryId: 31,
          limit: 0,
          currentValue: 0,
        },
      ],
    })
  }
}

export const budgetMock = new BudgetMock()
