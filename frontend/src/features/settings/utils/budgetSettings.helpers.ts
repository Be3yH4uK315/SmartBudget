import { BudgetSettings } from '@features/budget/types'
import { FormValues } from '@shared/types/components'
import dayjs from 'dayjs'

export const canEditNextMonthBudget = () => {
  return dayjs().date() >= 2
}

export const getBudgetDateByStatus = (status: 'current' | 'next') => {
  return status === 'current'
    ? dayjs().format('YYYY-MM-DD')
    : dayjs().endOf('month').add(1, 'day').format('YYYY-MM-DD')
}

export const mapBudgetSettingsToForm = (
  data: Omit<BudgetSettings, 'totalLimit'> & { totalLimit: number | null },
): FormValues => ({
  totalLimit: data.totalLimit !== 0 ? data.totalLimit : null,
  isAutoRenew: data.isAutoRenew,
  categories: data.categories.map((c) => ({
    categoryId: c.categoryId,
    limit: c.limit,
    percent: undefined,
  })),
})
