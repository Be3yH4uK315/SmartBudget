import { TransactionsSliceState } from '@features/transactions/types'

export function getTransactionsInitialState(): TransactionsSliceState {
  return {
    transactions: [],
    isLoading: true,

    filters: {
      categoryIds: [],
      valueFrom: undefined,
      valueTo: undefined,
      dateFrom: '',
      dateTo: '',
      type: '',
    },

    offset: 0,
    isLast: false,
  }
}
