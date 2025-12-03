type DashboardResponsePayload = {
  goals: DashboardGoal[]

  categories: DashboardCategory[]

  budgetTotalLimit: number
}

type DashboardGoal = {
  name: string

  totalValue: number

  currentValue: number
}

type DashboardCategory = {
  categoryId: number

  value: number

  type: string
}

type normalizedCategory = {
  value: number

  label: string

  color: string
  
  lightColor: string
}

type FilterType = 'income' | 'expense'
