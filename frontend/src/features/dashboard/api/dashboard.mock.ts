import { DashboardCategory, DashboardGoal } from '@features/dashboard/types'

const goalNames: string[] = ['Новая машина', 'Отпуск', 'Квартира', 'Образование']
const categoryIds = Array.from({ length: 10 }, (_, i) => i + 1)

class DashboardMock {
  baseUrl = '/dashboard'

  private goals: DashboardGoal[] = goalNames.map((name, i) => ({
    name,
    targetAmount: 10000 + i * 5000,
    currentAmount: Math.floor(Math.random() * (10000 + i * 5000)),
  }))

  private categories: DashboardCategory[] = categoryIds.map((id) => ({
    categoryId: id,
    amount: Math.floor(Math.random() * 20000),
    transactionType: Math.random() > 0.5 ? 'income' : 'expense',
  }))

  private totalLimitAmount = 100000

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
    totalLimitAmount: number
  }> {
    console.log('%cMOCK CALL getDashboardBudget', 'color: orange')
    await this.delay(400)
    return {
      categories: [...this.categories],
      totalLimitAmount: this.totalLimitAmount,
    }
  }
}

export const dashboardMock = new DashboardMock()
