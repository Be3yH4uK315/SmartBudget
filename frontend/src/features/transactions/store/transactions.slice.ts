import { TransactionsSliceReducers, TransactionsSliceState } from '@features/transactions/types'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { PAGE_SIZE } from '../constants/transactionsPage'
import { groupByDate } from '../utils'
import { getTransactionsInitialState } from './transactions.state'
import { getTransactions } from './transactions.thunks'

export const transactionsSlice = createSlice<
  TransactionsSliceState,
  TransactionsSliceReducers,
  'transactions',
  any
>({
  name: 'transactions',
  initialState: getTransactionsInitialState(),
  reducers: {},

  extraReducers: (builder) => {
    builder
      .addCase(getTransactions.fulfilled, (state, { payload }) => {
        const length = payload.length

        if (length === 0) {
          state.isLoading = false
          state.isLast = true
          return
        }

        const blocks = groupByDate(payload.transactions)

        if (state.transactions.length === 0) {
          state.transactions = blocks
        } else {
          state.transactions = [
            ...state.transactions.slice(0, -1),
            {
              ...state.transactions[state.transactions.length - 1],
              transactions: [
                ...state.transactions[state.transactions.length - 1].transactions,
                ...blocks[0].transactions,
              ],
            },
            ...blocks.slice(1),
          ]
        }

        state.offset += length
        state.isLoading = false

        if (length < PAGE_SIZE) {
          state.isLast = true
        }
      })

      .addCase(getTransactions.rejected, (state) => {
        state.isLoading = false
      })

      .addCase(getTransactions.pending, (state) => {
        state.isLoading = true
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof transactionsSlice> {}
}

transactionsSlice.injectInto(rootReducer)
