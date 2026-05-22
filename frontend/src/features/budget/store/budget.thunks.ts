import { budgetApi } from '@features/budget/api'
import { BudgetPayload, BudgetSettings } from '@features/budget/types'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { showToast } from '@shared/utils'

export const getBudgetData = createAsyncThunk<
  BudgetPayload,
  void,
  { rejectValue: 'cannotGetBudgetData' }
>('getBudgetData', async (_, { rejectWithValue }) => {
  try {
    const response = await budgetApi.getBudgetData()

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetBudgetData', type: 'error' })

    return rejectWithValue('cannotGetBudgetData')
  }
})

export const createBudget = createAsyncThunk<
  BudgetPayload,
  { payload: BudgetSettings },
  { rejectValue: 'cannotCreateBudget' }
>('createBudget', async ({ payload }, { rejectWithValue }) => {
  try {
    await budgetApi.createBudget(payload)

    const realData = await budgetApi.getBudgetData()

    showToast({ messageKey: 'budgetCreated', type: 'success' })
    return realData
  } catch (e: any) {
    showToast({ messageKey: 'cannotCreateBudget', type: 'error' })

    return rejectWithValue('cannotCreateBudget')
  }
})
