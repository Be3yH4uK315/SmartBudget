import { transactionsApi } from '@features/transactions/api/transactions.api'
import { transactionsMock } from '@features/transactions/api/transactions.mock'
import { Transaction, TransactionsBlock } from '@features/transactions/types'
import { groupByDate } from '@features/transactions/utils'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { selectUser } from '@shared/store'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getTransactions = createAsyncThunk<
  { transactions: Transaction[]; length: number },
  void,
  { state: RootState }
>('getTransactions', async (_, { getState }) => {
  try {
    const state = getState()

    if (!state.transactions) {
      showToast({ messageKey: 'cannotGetTransactions', type: 'error', duration: 5000 })

      return { transactions: [], length: 0 }
    }

    const offset = state.transactions?.offset

    const response = await transactionsMock.getTransactions(offset)

    return { transactions: response, length: response.length }
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetTransactions', type: 'error', duration: 5000 })

    return { transactions: [], length: 0 }
  }
})

export const changeCategory = createAsyncThunk<void, Transaction, { state: RootState }>(
  'changeCategory',
  async (payload, { getState }) => {
    try {
      const userid = selectUser(getState()).userId
      const data = {
        userId: userid,
        payload,
      }
      const response = await transactionsApi.changeCategory(data)

      return response
    } catch (e: any) {
      showToast({ messageKey: 'cannotChangeCategory', type: 'error', duration: 5000 })
    }
  },
)
