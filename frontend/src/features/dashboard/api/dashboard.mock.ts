import { DashboardCategory, DashboardGoal } from '@features/dashboard/types'

const goalNames = ['Новая машина', 'Отпуск', 'Квартира', 'Образование']
const categoryIds = Array.from({ length: 10 }, (_, i) => i + 1)

class DashboardMock {
  baseUrl = '/dashboard'

  private goals: DashboardGoal[] = goalNames.map((name, i) => ({
    name,
    totalValue: 10000 + i * 5000,
    currentValue: Math.floor(Math.random() * (10000 + i * 5000)),
  }))

  private categories: DashboardCategory[] = categoryIds.map((id) => ({
    categoryId: id,
    value: Math.floor(Math.random() * 20000),
    type: Math.random() > 0.5 ? 'income' : 'expense',
  }))

  private budgetTotalLimit = 100000

  private delay(ms = 500) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  async getDashboardGoals(): Promise<DashboardGoal[]> {
    console.log('%cMOCK CALL getDashboardGoals', 'color: orange')
    await this.delay(400)
    return [...this.goals]
  }

  async getDashboardBudget(): Promise<{
    categories: DashboardCategory[]
    budgetTotalLimit: number
  }> {
    console.log('%cMOCK CALL getDashboardBudget', 'color: orange')
    await this.delay(400)
    return {
      categories: [...this.categories],
      budgetTotalLimit: this.budgetTotalLimit,
    }
  }
}

export const dashboardMock = new DashboardMock()
