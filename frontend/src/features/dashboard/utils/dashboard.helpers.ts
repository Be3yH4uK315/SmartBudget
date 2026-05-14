import { DashboardCategory } from '@features/dashboard/types'

export const calcBudgetStats = (categories: DashboardCategory[]) => {
  return categories.reduce((sum, c) => {
    if (c.transactionType === 'expense') return (sum += c.amount)
    return sum
  }, 0)
}
