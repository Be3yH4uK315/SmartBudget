import { CategoryRow } from '@features/budget/hooks'
import { CreateBudgetPayload } from '@features/budget/types'

type FormValues = {
  totalLimit: number
  isAutoRenew: boolean
  categories: CategoryRow[]
}

export const mapFormToCreateBudgetPayload = (values: FormValues): CreateBudgetPayload => {
  return {
    totalLimit: values.totalLimit,
    isAutoRenew: values.isAutoRenew,
    categories: values.categories
      .filter((c) => c.categoryId !== null && c.limit > 0)
      .map((c) => ({
        categoryId: c.categoryId,
        limit: c.limit,
      })),
  }
}
