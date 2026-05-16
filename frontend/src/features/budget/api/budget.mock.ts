import { BudgetPayload } from '@features/budget/types'

class BudgetMock {
  async getBudgetData(): Promise<BudgetPayload> {
    await new Promise((r) => setTimeout(r, 800))

    return {
      totalLimitAmount: 14000,
      totalIncomeAmount: 0,
      totalSpentAmount: 2200,
      isAutoRenew: true,
      categories: [
        {
          categoryId: 1,
          limitAmount: 0,
          amount: 2000,
          transactionType: 'expense',
        },
        {
          categoryId: 2,
          limitAmount: 0,
          amount: 2004,
          transactionType: 'expense',
        },
        {
          categoryId: 3,
          limitAmount: 0,
          amount: 2000,
          transactionType: 'expense',
        },
        {
          categoryId: 4,
          limitAmount: 0,
          amount: 200,
          transactionType: 'expense',
        },
      ],
    }
  }
}

export const budgetMock = new BudgetMock()
