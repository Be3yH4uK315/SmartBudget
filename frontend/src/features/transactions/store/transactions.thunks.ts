import { transactionsApi } from '@features/transactions/api/transactions.api'
import { transactionsMock } from '@features/transactions/api/transactions.mock'
import { Transaction } from '@features/transactions/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
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

    const response = await transactionsApi.getTransactions(offset)

    return { transactions: response, length: response.length }
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetTransactions', type: 'error', duration: 5000 })

    return { transactions: [], length: 0 }
  }
})

export const changeCategory = createAsyncThunk<
  void,
  Pick<Transaction, 'categoryId' | 'transactionId'>,
  { state: RootState; rejectValue: string }
>('changeCategory', async (payload, { rejectWithValue }) => {
  try {
    const response = await transactionsApi.changeCategory(payload)

    showToast({ messageKey: 'categoryChanged', type: 'success', duration: 5000 })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotChangeCategory', type: 'error', duration: 5000 })

    return rejectWithValue('cannotChangeCategory')
  }
})
