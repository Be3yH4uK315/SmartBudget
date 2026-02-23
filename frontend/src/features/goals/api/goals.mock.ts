import {
  EditGoalPayload,
  Goal,
  GoalSearchOption,
  GoalsFilters,
  GoalStatus,
  GoalTransaction,
  Priority,
  SimplifiedGoal,
  Tag,
  UpdateGoalStatusPayload,
} from '@features/goals/types'

function generateMockGoals(total = 0): Goal[] {
  const statuses: GoalStatus[] = ['ongoing', 'achieved', 'expired', 'closed']
  const priorities: (Priority | null)[] = ['High', 'Medium', 'Low', null]
  const availableTags: Tag[] = ['Health', 'Education', 'Sport', 'Travel', 'Family']

  return Array.from({ length: total }, (_, i) => {
    const targetValue = 100000 + i * 25000
    const currentValue = Math.round(Math.random() * targetValue)

    return {
      goalId: `goal_${i}_${Math.random().toString(36).slice(2, 8)}`,
      name: `Цель #${i}`,
      targetValue,
      currentValue,
      status: statuses[i % statuses.length],
      isArchived: i % 3 !== 0,
      tags: availableTags.slice(0, i % availableTags.length),
      priority: priorities[i % priorities.length],
      finishDate: i % 2 === 0 ? '2026-12-31' : null,
      daysLeft: i % 2 === 0 ? 120 - i * 3 : null,
      recommendedPayment: i % 2 === 0 ? Math.round((targetValue - currentValue) / 6) : null,
    }
  })
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
    await new Promise((r) => setTimeout(r, 800))

    let result = [...ALL_GOALS]

    if (filters?.tags?.length) {
      result = result.filter((g) => filters.tags.every((t) => g.tags.includes(t as Tag)))
    }

    if (filters?.priority?.length) {
      result = result.filter((g) => filters.priority.includes(g.priority as Priority))
    }

    if (filters?.isArchived) {
      result = result.filter((g) => g.isArchived === true)
    } else {
      result = result.filter((g) => g.isArchived === false)
    }

    return result.map(({ daysLeft, recommendedPayment, ...rest }) => rest)
  }

  async getGoal(goalId: string): Promise<Goal> {
    console.log('%cMOCK CALL getGoal ' + goalId, 'color: orange')
    await new Promise((r) => setTimeout(r, 600))

    const goal = ALL_GOALS.find((g) => g.goalId === goalId)
    if (!goal) throw new Error('Goal not found')
    return goal
  }

  async getGoalTransactions(goalId: string): Promise<GoalTransaction[]> {
    console.log('%cMOCK CALL getGoalTransactions ' + goalId, 'color: orange')
    await new Promise((r) => setTimeout(r, 600))

    return GOAL_TRANSACTIONS_MAP[goalId] ?? []
  }

  async editGoal(payload: EditGoalPayload): Promise<void> {
    console.log('%cMOCK CALL editGoal', 'color: orange', payload)
    await new Promise((r) => setTimeout(r, 800))

    const index = ALL_GOALS.findIndex((g) => g.goalId === payload.goalId)
    if (index === -1) return

    ALL_GOALS[index] = {
      ...ALL_GOALS[index],
      ...payload,
    }
  }

  async createGoal(payload: Omit<EditGoalPayload, 'goalId'>): Promise<{ goalId: string }> {
    console.log('%cMOCK CALL createGoal', 'color: orange', payload)
    await new Promise((r) => setTimeout(r, 800))

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

  async updateGoalStatus({
    goalId,
    status,
  }: UpdateGoalStatusPayload): Promise<{ status: GoalStatus }> {
    console.log('%cMOCK CALL updateGoalStatus', 'color: orange', {
      goalId,
      status,
    })

    await new Promise((r) => setTimeout(r, 600))

    const goal = ALL_GOALS.find((g) => g.goalId === goalId)
    if (!goal) throw new Error('Goal not found')

    goal.status = status
    return { status }
  }

  async updateArchivedStatus(goalId: string): Promise<{ isArchived: boolean }> {
    console.log('%cMOCK CALL updateArchivedStatus', 'color: orange', goalId)
    await new Promise((r) => setTimeout(r, 600))

    const goal = ALL_GOALS.find((g) => g.goalId === goalId)
    if (!goal) throw new Error('Goal not found')

    goal.isArchived = !goal.isArchived
    return { isArchived: goal.isArchived }
  }

  searchGoals = async (
    query: string,
    signal?: AbortSignal,
    limit = 10,
  ): Promise<GoalSearchOption[]> => {
    console.log('%cMOCK CALL searchGoals', 'color: orange', { query })

    const requestId = Date.now()
    let canceled = false

    if (signal) {
      signal.addEventListener('abort', () => {
        canceled = true
      })
    }

    await new Promise((r) => setTimeout(r, 400))
    if (canceled) return []

    const normalizedQuery = query.trim().toLowerCase()
    if (!normalizedQuery) return []

    const results: GoalSearchOption[] = ALL_GOALS.filter((g) =>
      g.name.toLowerCase().includes(normalizedQuery),
    )
      .slice(0, limit)
      .map(({ goalId, name, targetValue, currentValue, status, isArchived }) => ({
        goalId,
        name,
        targetValue,
        currentValue,
        status,
        isArchived,
      }))

    return results
  }
}

export const goalsMock = new GoalsMock()
