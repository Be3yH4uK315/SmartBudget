import { BudgetSettings } from '@features/budget/types'
import { FormValues } from '@shared/types/components'
import dayjs from 'dayjs'

export const canEditNextMonthBudget = () => {
  return dayjs().date() >= 2
}

export const mapBudgetSettingsToForm = (
  data: Omit<BudgetSettings, 'totalLimitAmount'> & { totalLimitAmount: number | null },
): FormValues => ({
  totalLimitAmount: data.totalLimitAmount !== 0 ? data.totalLimitAmount : null,
  isAutoRenew: data.isAutoRenew,
  categories: data.categories.map((c) => ({
    categoryId: c.categoryId,
    limitAmount: c.limitAmount,
    percent: undefined,
  })),
})
