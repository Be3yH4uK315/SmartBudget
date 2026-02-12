import { BudgetSettings } from '@features/budget/types'
import { FormValues } from '@shared/types/components'

export const mapFormToBudgetPayload = (values: FormValues): BudgetSettings => {
  return {
    totalLimit: values.totalLimit ?? 0,
    isAutoRenew: values.isAutoRenew,
    categories: values.categories.flatMap((c) => {
      if (c.categoryId == null || c.limit == null) {
        return []
      }

      return [
        {
          categoryId: c.categoryId,
          limit: c.limit ?? 0,
        },
      ]
    }),
  }
}
