export type DashboardGoal = {
  name: string

  targetAmount: number

  currentAmount: number
}

export type DashboardCategory = {
  categoryId: number

  value: number

  type: 'income' | 'expense'
}
