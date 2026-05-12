import { BudgetPayload } from '@features/budget/types'

class BudgetMock {
  async getBudgetData(): Promise<BudgetPayload> {
    await new Promise((r) => setTimeout(r, 800))

    return {
      totalLimitAmount: 12000,
      spentAmount: 26000,
      isAutoRenew: true,
      categories: [
        {
          categoryId: 1,
          limitAmount: 0,
          spentAmount: 2000,
        },
        {
          categoryId: 2,
          limitAmount: 2000,
          spentAmount: 2000,
        },
        {
          categoryId: 4,
          limitAmount: 2001,
          spentAmount: 2000,
        },
        {
          categoryId: 5,
          limitAmount: 0,
          spentAmount: 20000,
        },
        {
          categoryId: 31,
          limitAmount: 0,
          spentAmount: 0,
        },
      ],
    }
  }
}

export const budgetMock = new BudgetMock()
