import { TransactionsSliceState } from '@features/transactions/types'

export function getTransactionsInitialState(): TransactionsSliceState {
  return {
    transactions: [],
    isLoading: true,

    offset: 0,
    isLast: false,
  }
}
