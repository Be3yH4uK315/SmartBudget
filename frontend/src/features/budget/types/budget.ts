export type BudgetPayload = {
  categories: Category[]

  totalLimit: number

  currentValue: number

  isAutoRenew: boolean
}

export type Category = {
  categoryId: number

  limit: number

  currentValue: number
}

export type CreateBudgetPayload = {
  totalLimit: number

  isAutoRenew: boolean

  categories: Omit<Category, 'currentValue'>[]
}
