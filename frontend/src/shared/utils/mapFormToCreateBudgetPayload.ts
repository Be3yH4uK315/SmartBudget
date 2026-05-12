import { BudgetSettings } from '@features/budget/types'
import { FormValues } from '@shared/types/components'

export const mapFormToBudgetPayload = (values: FormValues): BudgetSettings => {
  return {
    totalLimitAmount: values.totalLimitAmount ?? 0,
    isAutoRenew: values.isAutoRenew,
    categories: values.categories.flatMap((c) => {
      if (c.categoryId == null || c.limitAmount == null) {
        return []
      }

      return [
        {
          categoryId: c.categoryId,
          limitAmount: c.limitAmount ?? 0,
        },
      ]
    }),
  }
}
