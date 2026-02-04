import { TransactionsSliceState } from '@features/transactions/types'

export function getTransactionsInitialState(): TransactionsSliceState {
  return {
    transactions: [],
    isLoading: true,

    searchTransactions: [],
    isSearchLoading: false,

    offset: 0,
    isLast: false,
  }
}
