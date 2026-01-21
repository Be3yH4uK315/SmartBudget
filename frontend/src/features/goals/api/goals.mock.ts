import {
  EditGoalPayload,
  Goal,
  GoalsFilters,
  GoalStatus,
  GoalTransaction,
  Priority,
  SimplifiedGoal,
  Tag,
} from '@features/goals/types'
import { PRIORITIES } from '../constants/tags'

function generateMockGoals(total = 0): Goal[] {
  const statuses: GoalStatus[] = ['ongoing', 'achieved', 'expired', 'closed']
  const priorities: (Priority | null)[] = ['High', 'Medium', 'Low', null]
  const availableTags: Tag[] = ['Health', 'Education', 'Sport', 'Travel', 'Family']

  const result: Goal[] = []

  for (let i = 0; i < total; i++) {
    const targetValue = 100000 + i * 25000
    const currentValue = Math.round(Math.random() * targetValue)
    const priority = priorities[i % priorities.length]

    const tags: Tag[] = []
    tags.push(...availableTags.slice(0, i % availableTags.length))

    result.push({
      goalId: `goal_${i}_${Math.random().toString(36).slice(2, 8)}`,
      name: `Цель#${i}Цель#Цель`,
      targetValue,
      currentValue,
      status: statuses[i % statuses.length],
      isArchived: i % 3 !== 0,
      tags,
      priority: priority ?? null,
      finishDate: i % 2 === 0 ? '2026-12-31' : null,
      daysLeft: i % 2 === 0 ? 120 - i * 3 : null,
      recommendedPayment: i % 2 === 0 ? Math.round((targetValue - currentValue) / 6) : null,
    })
  }

  return result
}

function generateMockGoalTransactions(goalId: string, total = 20): GoalTransaction[] {
  const types = ['income', 'expense'] as const
  const dates = [
    '2025-11-12T12:12:12',
    '2025-12-11T12:12:12',
    '2025-10-10T12:12:12',
    '2025-09-09T12:12:12',
    '2025-08-08T12:12:12',
  ]

  return Array.from({ length: total }, (_, i) => ({
    date: dates[i % dates.length],
    value: Math.round(Math.random() * 10000),
    type: types[i % types.length],
  }))
}

const ALL_GOALS = generateMockGoals(12)
const GOAL_TRANSACTIONS_MAP: Record<string, GoalTransaction[]> = {}
ALL_GOALS.forEach((g) => {
  GOAL_TRANSACTIONS_MAP[g.goalId] = generateMockGoalTransactions(g.goalId, 25)
})

class GoalsMock {
  baseUrl = '/goals'

  async getGoals(filters?: GoalsFilters): Promise<SimplifiedGoal[]> {
    console.log('%cMOCK CALL getGoals', 'color: orange', filters)

    await new Promise((resolve) => setTimeout(resolve, 800))

    let filteredGoals = [...ALL_GOALS]

    if (filters?.tags?.length) {
      filteredGoals = filteredGoals.filter((g) =>
        filters.tags.every((tag) => {
          if (PRIORITIES.includes(tag as (typeof PRIORITIES)[number])) {
            return g.priority === tag
          }

          return g.tags.includes(tag as Tag)
        }),
      )
    }

    if (typeof filters?.isArchived === 'boolean') {
      filteredGoals = filteredGoals.filter((g) => g.isArchived === filters.isArchived)
    }

    return filteredGoals.map(({ daysLeft, recommendedPayment, ...rest }) => rest)
  }

  async getGoal(goalId: string): Promise<Goal> {
    console.log('%cMOCK CALL getGoal ' + goalId, 'color: orange')
    await new Promise((resolve) => setTimeout(resolve, 600))

    const goal = ALL_GOALS.find((g) => g.goalId === goalId)
    if (!goal) throw new Error('Goal not found')
    return goal
  }

  async getGoalTransactions(goalId: string): Promise<GoalTransaction[]> {
    console.log('%cMOCK CALL getGoalTransactions ' + goalId, 'color: orange')
    await new Promise((resolve) => setTimeout(resolve, 600))

    return GOAL_TRANSACTIONS_MAP[goalId] ?? []
  }

  async editGoal(payload: EditGoalPayload): Promise<void> {
    console.log('%cMOCK CALL editGoal', 'color: orange', payload)
    await new Promise((resolve) => setTimeout(resolve, 800))

    const index = ALL_GOALS.findIndex((g) => g.goalId === payload.goalId)
    if (index === -1) return
    ALL_GOALS[index] = { ...ALL_GOALS[index], ...payload }
  }

  async createGoal(payload: Omit<EditGoalPayload, 'goalId'>): Promise<{ goalId: string }> {
    console.log('%cMOCK CALL createGoal', 'color: orange', payload)
    await new Promise((resolve) => setTimeout(resolve, 800))

    const goalId = `goal_${Date.now()}`
    ALL_GOALS.unshift({
      goalId,
      name: payload.name,
      targetValue: payload.targetValue,
      currentValue: 0,
      status: 'ongoing',
      isArchived: false,
      tags: payload.tags,
      priority: payload.priority ?? null,
      finishDate: payload.finishDate,
      daysLeft: 180,
      recommendedPayment: Math.round(payload.targetValue / 6),
    })

    GOAL_TRANSACTIONS_MAP[goalId] = []
    return { goalId }
  }

  async updateGoalStatus({ goalId, status }: { goalId: string; status: GoalStatus }) {
    console.log('%cMOCK CALL updateGoalStatus', 'color: orange', { goalId, status })
    await new Promise((resolve) => setTimeout(resolve, 600))

    const goal = ALL_GOALS.find((g) => g.goalId === goalId)
    if (!goal) throw new Error('Goal not found')
    goal.status = status
    return { status }
  }

  async updateArchivedStatus(goalId: string): Promise<{ isArchived: boolean }> {
    console.log('%cMOCK CALL updateArchivedStatus', 'color: orange', goalId)
    await new Promise((resolve) => setTimeout(resolve, 600))

    const goal = ALL_GOALS.find((g) => g.goalId === goalId)
    if (!goal) throw new Error('Goal not found')
    goal.isArchived = !goal.isArchived
    return { isArchived: goal.isArchived }
  }
}

export const goalsMock = new GoalsMock()
