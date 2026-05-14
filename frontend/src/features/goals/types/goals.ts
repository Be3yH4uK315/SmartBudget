import { AVAILABLE_TAGS, PRIORITIES } from '@features/goals/constants'

export type GoalStatus = 'ongoing' | 'achieved' | 'expired' | 'closed'

export type Goal = {
  goalId: string
  name: string
  targetAmount: number
  currentAmount: number
  status: GoalStatus
  isArchived: boolean
  tags: Tag[]
  priority: Priority | null
  finishDate: string | null
  daysLeft: number | null
  recommendedPayment: number | null
}

export type SimplifiedGoal = Omit<Goal, 'daysLeft' | 'recommendedPayment'>

export type GoalTransaction = {
  periodStart: string
  amount: number
  transactionType: 'income' | 'expense'
}

export type EditGoalPayload = {
  goalId: string
  name: string
  targetAmount: number
  tags: Tag[]
  priority: Priority | null
  status: GoalStatus
  finishDate: string | null
}

export type GoalsStats = {
  targetAmount: number
  currentAmount: number
}

export type ModalFormValues = {
  name: string
  targetAmount: number | ''
  finishDate: string | null
  tags: Tag[]
  priority: Priority | null
}

export type UpdateGoalStatusPayload = Pick<Goal, 'goalId' | 'status'>

export type GoalsFilters = {
  tags: Tag[]
  priority: Priority[]
  isArchived: boolean
}

export type GoalSearchOption = Omit<SimplifiedGoal, 'tags' | 'priority' | 'finishDate'>

export type Priority = (typeof PRIORITIES)[number]
export type Tag = (typeof AVAILABLE_TAGS)[number]
