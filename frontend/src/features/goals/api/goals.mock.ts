import { CurrentGoal, EditGoalPayload, Goal, GoalTransaction } from '../types/goals'

const delay = (ms = 300) => new Promise((resolve) => setTimeout(resolve, ms))

const today = new Date()

const calcDaysLeft = (finishDate: string) => {
  const finish = new Date(finishDate)
  const diff = finish.getTime() - today.getTime()
  return Math.max(Math.ceil(diff / (1000 * 60 * 60 * 24)), 0)
}

const goals: Goal[] = [
  {
    goalId: '1',
    name: 'Подарок маме',
    targetValue: 200000,
    currentValue: 75000,
    finishDate: '2026-01-18',
    status: 'ongoing',
  },
  {
    goalId: '2',
    name: 'Стиральная машина',
    targetValue: 50000,
    currentValue: 5000,
    finishDate: '2026-08-21',
    status: 'ongoing',
  },
  {
    goalId: '3',
    name: 'Квартира',
    targetValue: 150000000,
    currentValue: 140000,
    finishDate: '2024-08-21',
    status: 'closed',
  },
  {
    goalId: '4',
    name: 'Подарок на день рождения',
    targetValue: 150000,
    currentValue: 150000,
    finishDate: '2024-08-21',
    status: 'achieved',
  },
  {
    goalId: '5',
    name: 'Отпуск',
    targetValue: 150000,
    currentValue: 140000,
    finishDate: '2024-08-18',
    status: 'expired',
  },
]

const goalTransactions: Record<string, GoalTransaction[]> = {
  '1': [
    {
      date: '2024-01-10',
      value: 30000,
      type: 'income',
    },
    {
      date: '2024-02-15',
      value: 45000,
      type: 'income',
    },
  ],
  '2': [
    {
      date: '2024-03-01',
      value: 150000,
      type: 'income',
    },
  ],
}

class GoalsApiMock {
  async getGoals(): Promise<Goal[]> {
    await delay()
    return goals
  }

  async getGoal(goalId: string): Promise<CurrentGoal> {
    await delay()

    const goal = goals.find((g) => g.goalId === goalId)
    if (!goal) {
      throw new Error('Goal not found')
    }

    return {
      ...goal,
      daysLeft: calcDaysLeft(goal.finishDate),
      transactions: goalTransactions[goalId] ?? [],
    }
  }

  async editGoal(payload: EditGoalPayload): Promise<void> {
    await delay()

    const index = goals.findIndex((g) => g.goalId === payload.goalId)
    if (index === -1) {
      throw new Error('Goal not found')
    }

    goals[index] = {
      ...goals[index],
      name: payload.name,
      targetValue: payload.targetValue,
      finishDate: payload.finishDate,
    }
  }

  async createGoal(payload: Omit<EditGoalPayload, 'goalId'>): Promise<string> {
    await delay()

    const goalId = Date.now().toString()

    const newGoal: Goal = {
      goalId,
      name: payload.name,
      targetValue: payload.targetValue,
      currentValue: 0,
      finishDate: payload.finishDate,
      status: 'ongoing',
    }

    goals.push(newGoal)
    goalTransactions[goalId] = []

    return goalId
  }
}

export const goalsMock = new GoalsApiMock()
