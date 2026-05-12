import { STATUS_PRIORITY } from '@features/goals/constants/sortOrder'
import { GoalsStats, SimplifiedGoal } from '@features/goals/types'

export function getGoalsStats(goals: SimplifiedGoal[]): GoalsStats {
  const { targetAmount, currentAmount } = goals.reduce<GoalsStats>(
    (acc, goal) => {
      acc.currentAmount += goal.currentAmount
      acc.targetAmount += goal.targetAmount

      return acc
    },
    {
      targetAmount: 0,
      currentAmount: 0,
    },
  )

  return { targetAmount, currentAmount }
}

export const sortGoals = (goals: SimplifiedGoal[]): SimplifiedGoal[] =>
  [...goals].sort((a, b) => {
    const statusDiff = STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status]

    if (statusDiff !== 0) {
      return statusDiff
    }

    return b.currentAmount / b.targetAmount - a.currentAmount / a.targetAmount
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
