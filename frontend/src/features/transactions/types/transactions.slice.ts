import { SliceCaseReducers } from '@shared/types'
import { TransactionsBlock } from './transactions'

export type TransactionsSliceState = {
  transactions: TransactionsBlock[]
  isLoading: boolean

  isCategoryChanging: boolean

  offset: number
  isLast: boolean
}

export type TransactionsSliceReducers = SliceCaseReducers<TransactionsSliceState> & {
  clearTransactionsState(state: TransactionsSliceState): void
}
