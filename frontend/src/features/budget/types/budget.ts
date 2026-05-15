export type BudgetPayload = {
  categories: Category[]

  totalLimitAmount: number
  totalSpentAmount: number
  totalIncomeAmount: number

  isAutoRenew: boolean
}

export type Category = {
  categoryId: number

  limitAmount: number

  amount: number

  transactionType: 'expense' | 'income'
}

export type BudgetSettings = {
  totalLimitAmount: number

  isAutoRenew: boolean

  categories: Omit<Category, 'amount' | 'transactionType'>[]
}
