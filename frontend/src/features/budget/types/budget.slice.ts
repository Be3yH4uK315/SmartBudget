import { SliceCaseReducers } from '@shared/types/reduxToolkit'
import { Category } from './budget'

export type BudgetSliceState = {
  budgetId: string | null
  isLoading: boolean

  totalLimitAmount: number

  totalIncomeAmount: number

  isAutoRenew: boolean

  categories: Category[]
}

export type BudgetSliceReducers = SliceCaseReducers<BudgetSliceState> & {
  clearBudgetState(state: BudgetSliceState): void
}
