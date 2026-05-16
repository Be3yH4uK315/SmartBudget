import { BudgetSettings } from '@features/budget/types'
import { settingsApi, settingsMock } from '@features/settings/api'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { showToast } from '@shared/utils'

export const getBudgetSettings = createAsyncThunk<
  BudgetSettings,
  string,
  { rejectValue: 'cannotGetBudgetSettings' }
>('getBudgetSettings', async (date, { rejectWithValue }) => {
  try {
    const response = await settingsApi.getBudgetSettings(date)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetBudgetSettings', type: 'error' })

    return rejectWithValue('cannotGetBudgetSettings')
  }
})

export const setBudgetSettings = createAsyncThunk<
  void,
  BudgetSettings,
  { rejectValue: 'cannotSetBudgetSettings' }
>('setBudgetSettings', async (payload, { rejectWithValue }) => {
  try {
    const response = await settingsApi.setBudgetSettings(payload)

    showToast({ messageKey: 'budgetSettingsSet', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotSetBudgetSettings', type: 'error' })

    return rejectWithValue('cannotSetBudgetSettings')
  }
})
