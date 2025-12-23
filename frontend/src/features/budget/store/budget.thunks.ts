import { budgetApi, budgetMock } from '@features/budget/api'
import { BudgetPayload, CreateBudgetPayload } from '@features/budget/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { showToast } from '@shared/utils'

export const getBudgetData = createAsyncThunk<
  BudgetPayload,
  void,
  { rejectValue: 'cannotGetBudgetData' }
>('getBudgetData', async (_, { rejectWithValue }) => {
  try {
    const response = await budgetMock.getBudgetData()

    return response
  } catch (e: any) {
    return rejectWithValue('cannotGetBudgetData')
  }
})

export const createBudget = createAsyncThunk<
  void,
  { payload: CreateBudgetPayload },
  { rejectValue: 'cannotCreateBudget' }
>('createBudget', async ({ payload }, { rejectWithValue }) => {
  try {
    await budgetApi.createBudget(payload)

    showToast({ messageKey: 'budgetCreated', type: 'success' })
  } catch (e: any) {
    return rejectWithValue('cannotCreateBudget')
  }
})
