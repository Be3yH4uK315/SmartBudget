import { DashboardCategory } from '@features/dashboard/types'
import { GoalTransaction } from '@features/goals/types'
import { TransactionBase } from '@shared/types/components'
import dayjs from 'dayjs'

export const mapDashboardCategory = (item: DashboardCategory): TransactionBase => ({
  value: item.value,
  type: item.type,
  categoryId: item.categoryId,
})

export const mapGoalTransaction = (item: GoalTransaction): TransactionBase => ({
  value: item.value,
  type: item.type,
  month: Number(dayjs(item.date).format('M')),
})
