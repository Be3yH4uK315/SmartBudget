export type DashboardResponsePayload = {
  goals: DashboardGoal[]

  categories: DashboardCategory[]

  budgetTotalLimit: number
}

export type DashboardGoal = {
  name: string

  totalValue: number

  currentValue: number
}

export type DashboardCategory = {
  categoryId: number

  value: number

  type: string
}

export type normalizedCategory = {
  value: number

  label: string

  color: string

  lightColor: string
}

export type FilterType = 'income' | 'expense'
