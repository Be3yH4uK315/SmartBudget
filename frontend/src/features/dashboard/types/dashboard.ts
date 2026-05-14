export type DashboardGoal = {
  name: string

  targetAmount: number

  currentAmount: number
}

export type DashboardCategory = {
  categoryId: number

  amount: number

  transactionType: 'income' | 'expense'
}
