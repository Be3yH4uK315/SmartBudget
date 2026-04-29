import { STATUS_PRIORITY } from '@features/goals/constants/sortOrder'
import { GoalsStats, SimplifiedGoal } from '@features/goals/types'

export function getGoalsStats(goals: SimplifiedGoal[]): GoalsStats {
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

export const sortGoals = (goals: SimplifiedGoal[]): SimplifiedGoal[] =>
  [...goals].sort((a, b) => {
    const statusDiff = STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status]

    if (statusDiff !== 0) {
      return statusDiff
    }

    return b.currentValue / b.targetValue - a.currentValue / a.targetValue
  })

export const pushIntoSorted = (
  goals: SimplifiedGoal[],
  newGoal: SimplifiedGoal,
): SimplifiedGoal[] => {
  const result = [...goals]
  const index = result.findIndex((g) => sortGoals([newGoal, g])[0] === newGoal)

  if (index === -1) {
    result.push(newGoal)
  } else {
    result.splice(index, 0, newGoal)
  }

  return result
}
