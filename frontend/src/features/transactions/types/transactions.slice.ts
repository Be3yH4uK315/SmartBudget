import { SliceCaseReducers } from '@shared/types'
import { Transaction, TransactionsBlock } from './transactions'

export type TransactionsSliceState = {
  transactions: TransactionsBlock[]
  isLoading: boolean

  searchTransactions: Transaction[]
  isSearchLoading: boolean

  offset: number
  isLast: boolean
}

export type TransactionsSliceReducers = SliceCaseReducers<TransactionsSliceState> & {
  clearTransactionsState(state: TransactionsSliceState): void
}
