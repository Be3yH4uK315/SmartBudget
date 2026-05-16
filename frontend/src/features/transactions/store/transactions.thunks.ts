import { transactionsApi, transactionsMock } from '@features/transactions/api'
import {
  GoalId,
  ManualTransaction,
  Transaction,
  TransactionsFilters,
} from '@features/transactions/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { RootState } from '@shared/types'
import { showToast } from '@shared/utils'

export const getTransactions = createAsyncThunk<
  { transactions: Transaction[]; length: number },
  TransactionsFilters,
  { state: RootState }
>('getTransactions', async (filters, { getState }) => {
  try {
    const state = getState()

    const offset = state.transactions?.offset ?? 0

    const response = await transactionsMock.getTransactions(offset, filters)

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
    const response = await transactionsApi.changeCategory(payload)

    showToast({ messageKey: 'categoryChanged', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotChangeCategory', type: 'error' })

    return rejectWithValue('cannotChangeCategory')
  }
})

export const addTransaction = createAsyncThunk<
  void,
  ManualTransaction,
  { state: RootState; rejectValue: string }
>('addTransaction', async (payload, { rejectWithValue }) => {
  try {
    const response = await transactionsApi.addTransaction(payload)

    showToast({ messageKey: 'transactionAdded', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotAddTransaction', type: 'error' })

    return rejectWithValue('cannotAddTransaction')
  }
})

export const importTransaction = createAsyncThunk<
  void,
  void,
  { state: RootState; rejectValue: string }
>('importTransaction', async (_, { rejectWithValue }) => {
  try {
    const response = await transactionsMock.importTransaction()

    showToast({ messageKey: 'transactionsImported', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotImportTransaction', type: 'error' })

    return rejectWithValue('cannotImportTransaction')
  }
})

export const getGoalsNames = createAsyncThunk<
  GoalId[],
  void,
  { state: RootState; rejectValue: string }
>('getGoalsNames', async (_, { rejectWithValue }) => {
  try {
    const response = await transactionsApi.getGoalsNames()

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetGoalsNames', type: 'error' })

    return rejectWithValue('cannotGetGoalsNames')
  }
})
