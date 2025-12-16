import { Goal } from '../types'

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
