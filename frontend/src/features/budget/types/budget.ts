export type BudgetPayload = {
  categories: Category[]

  totalLimitAmount: number

  spentAmount: number

  isAutoRenew: boolean
}

export type Category = {
  categoryId: number

  limitAmount: number

  spentAmount: number
}

export type BudgetSettings = {
  totalLimitAmount: number

  isAutoRenew: boolean

  categories: Omit<Category, 'spentAmount'>[]
}
