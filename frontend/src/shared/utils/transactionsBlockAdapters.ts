import { Category } from '@features/budget/types'
import { DashboardCategory } from '@features/dashboard/types'
import { GoalTransaction } from '@features/goals/types'
import { TransactionBase } from '@shared/types/components'
import dayjs from 'dayjs'

export const mapDashboardCategory = (item: DashboardCategory): TransactionBase => ({
  value: item.amount,
  type: item.transactionType,
  categoryId: item.categoryId,
})

export const mapGoalTransaction = (item: GoalTransaction): TransactionBase => ({
  value: item.amount,
  type: item.transactionType,
  month: Number(dayjs(item.periodStart).format('M')),
})

export const mapBudgetCategories = (item: Category): TransactionBase => ({
  value: item.amount,
  categoryId: item.categoryId,
  type: item.transactionType,
})

export const mapPlanedBudgetData = (item: Category): TransactionBase => ({
  value: item.limitAmount,
  categoryId: item.categoryId,
  type: 'expense',
})
