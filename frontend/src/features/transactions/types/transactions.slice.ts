import { SliceCaseReducers } from '@shared/types'
import { GoalId, TransactionsBlock } from './transactions'

export type TransactionsSliceState = {
  transactions: TransactionsBlock[]
  isLoading: boolean

  isCategoryChanging: boolean

  offset: number
  isLast: boolean
  isImportLoading: boolean

  availableGoals: GoalId[]
}

export type TransactionsSliceReducers = SliceCaseReducers<TransactionsSliceState> & {
  clearTransactionsState(state: TransactionsSliceState): void
  clearAvailableGoals(state: TransactionsSliceState): void
}
