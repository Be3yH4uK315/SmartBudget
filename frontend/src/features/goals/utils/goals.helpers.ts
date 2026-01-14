import { STATUS_PRIORITY } from '@features/goals/constants/sortOrder'
import { Goal } from '@features/goals/types'

type GoalsStats = {
  targetValue: number
  currentValue: number
}

export function getGoalsStats(goals: Goal[]): GoalsStats {
  const { targetValue, currentValue } = goals.reduce<GoalsStats>(
    (acc, goal) => {
      acc.currentValue += goal.currentValue
      acc.targetValue += goal.targetValue

      return acc
    },
    {
      targetValue: 0,
      currentValue: 0,
    },
  )

  return { targetValue, currentValue }
}

export const sortGoals = (goals: Goal[]): Goal[] =>
  [...goals].sort((a, b) => {
    const statusDiff = STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status]

    if (statusDiff !== 0) {
      return statusDiff
    }

    return b.currentValue / b.targetValue - a.currentValue / a.targetValue
  })

export const pushIntoSorted = (goals: Goal[], newGoal: Goal): Goal[] => {
  const result = [...goals]
  const index = result.findIndex((g) => sortGoals([newGoal, g])[0] === newGoal)

  if (index === -1) {
    result.push(newGoal)
  } else {
    result.splice(index, 0, newGoal)
  }

  return result
}
