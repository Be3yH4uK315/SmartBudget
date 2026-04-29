import { SliceCaseReducers } from '@shared/types/reduxToolkit'
import { Category } from './budget'

export type BudgetSliceState = {
  isLoading: boolean

  totalLimit: number

  currentValue: number

  isAutoRenew: boolean

  categories: Category[]
}

export type BudgetSliceReducers = SliceCaseReducers<BudgetSliceState> & {
  clearBudgetState(state: BudgetSliceState): void
}
