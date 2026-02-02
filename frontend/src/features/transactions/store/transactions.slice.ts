import { PAGE_SIZE } from '@features/transactions/constants/transactionsPage'
import { TransactionsSliceReducers, TransactionsSliceState } from '@features/transactions/types'
import { groupByDate, mergeTransactionBlocks } from '@features/transactions/utils'
import { createSlice, WithSlice } from '@reduxjs/toolkit'
import { rootReducer } from '@shared/store'
import { getTransactionsInitialState } from './transactions.state'
import { changeCategory, getTransactions } from './transactions.thunks'

export const transactionsSlice = createSlice<
  TransactionsSliceState,
  TransactionsSliceReducers,
  'transactions',
  any
>({
  name: 'transactions',
  initialState: getTransactionsInitialState(),
  reducers: {
    clearTransactionsState() {
      return getTransactionsInitialState()
    },
    resetFilters(state) {
      state.filters = {
        categoryIds: [],
        valueFrom: undefined,
        valueTo: undefined,
        dateFrom: '',
        dateTo: '',
        type: '',
      }
      state.offset = 0
      state.transactions = []
    },
    setCategoryIds(state, { payload }) {
      state.filters.categoryIds = payload
      state.offset = 0
      state.transactions = []
    },
    setType(state, { payload }) {
      state.filters.type = payload
      state.offset = 0
      state.transactions = []
    },
    setDateFrom(state, { payload }) {
      state.filters.dateFrom = payload
      state.offset = 0
      state.transactions = []
    },
    setDateTo(state, { payload }) {
      state.filters.dateTo = payload
      state.offset = 0
      state.transactions = []
    },
    setValueFrom(state, { payload }) {
      state.filters.valueFrom = payload
      state.offset = 0
      state.transactions = []
    },
    setValueTo(state, { payload }) {
      state.filters.valueTo = payload
      state.offset = 0
      state.transactions = []
    },
  },

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
          state.transactions = mergeTransactionBlocks({
            currentBlocks: state.transactions,
            newBlocks: blocks,
          })
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

      .addCase(changeCategory.fulfilled, (state, { meta }) => {
        const { categoryId, transactionId } = meta.arg

        for (const block of state.transactions) {
          const transaction = block.transactions.find((t) => t.transactionId === transactionId)
          if (transaction) {
            transaction.categoryId = categoryId
            break
          }
        }
      })
  },
})

declare module '@shared/store' {
  interface AppLazySlices extends WithSlice<typeof transactionsSlice> {}
}

transactionsSlice.injectInto(rootReducer)

export const {
  clearTransactionsState,
  resetFilters,
  setCategoryIds,
  setDateFrom,
  setDateTo,
  setType,
  setValueFrom,
  setValueTo,
} = transactionsSlice.actions
