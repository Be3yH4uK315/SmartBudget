import { DashboardResponsePayload } from '@features/dashboard/types'

class DashboardMock {
  baseUrl = ''

  async getDashboardData(): Promise<DashboardResponsePayload> {
    await new Promise((resolve) => setTimeout(resolve, 1000))
    return {
      goals: [
        { name: 'Квартира', targetValue: 10000000, currentValue: 100 },
        { name: 'Машина', targetValue: 2000000, currentValue: 200 },
      ],
      categories: [
        {
          categoryId: 1,
          value: 100,
          type: 'income',
        },
        {
          categoryId: 2,
          value: 200,
          type: 'expense',
        },
        {
          categoryId: 3,
          value: 300,
          type: 'expense',
        },
        {
          categoryId: 4,
          value: 400,
          type: 'income',
        },
        {
          categoryId: 5,
          value: 500,
          type: 'income',
        },
        {
          categoryId: 6,
          value: 600,
          type: 'income',
        },
        {
          categoryId: 7,
          value: 700,
          type: 'income',
        },
        {
          categoryId: 8,
          value: 800,
          type: 'income',
        },
      ],
      budgetTotalLimit: 20000,
    }
  }
}

export const dashboardMock = new DashboardMock()
