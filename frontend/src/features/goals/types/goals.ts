export type Goal = {
  goalId: string
  name: string
  targetValue: number
  currentValue: number
  finishDate: string
  status: 'ongoing' | 'achieved' | 'expired' | 'closed'
}

export type CurrentGoal = Goal & {
  daysLeft: number

  transactions: GoalTransaction[]
}

export type GoalTransaction = {
  date: string
  value: number
  type: 'income' | 'expense'
}

export type EditGoalPayload = {
  goalId: string
  name: string
  targetValue: number
  finishDate: string
}
