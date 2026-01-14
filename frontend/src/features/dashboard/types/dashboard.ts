export type DashboardResponsePayload = {
  goals: DashboardGoal[]

  categories: DashboardCategory[]

  budgetTotalLimit: number
}

export type DashboardGoal = {
  name: string

  targetValue: number

  currentValue: number
}

export type DashboardCategory = {
  categoryId: number

  value: number

  type: 'income' | 'expense'
}
