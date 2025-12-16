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

    const offset = state.transactions?.offset ?? 0

    const response = await transactionsMock.getTransactions(offset)

    return { transactions: response, length: response.length }
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetTransactions', type: 'error' })

    return { transactions: [], length: 0 }
  }
})

export const changeCategory = createAsyncThunk<
  void,
  Pick<Transaction, 'categoryId' | 'transactionId'>,
  { state: RootState; rejectValue: string }
>('changeCategory', async (payload, { rejectWithValue }) => {
  try {
    const response = await transactionsMock.changeCategory(payload)

    showToast({ messageKey: 'categoryChanged', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotChangeCategory', type: 'error' })

    return rejectWithValue('cannotChangeCategory')
  }
})
