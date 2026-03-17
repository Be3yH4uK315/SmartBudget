import { DashboardCategory } from '@features/dashboard/types'

export const calcBudgetStats = (categories: DashboardCategory[]) => {
  return categories.reduce((sum, c) => {
    if (c.type === 'expense') return (sum += c.value)
    return sum
  }, 0)
}
