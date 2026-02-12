import { BudgetSettings } from '@features/budget/types'
import { settingsApi, settingsMock } from '@features/settings/api'
import { createAsyncThunk } from '@reduxjs/toolkit'
import { showToast } from '@shared/utils'

export const getBudgetSettings = createAsyncThunk<
  BudgetSettings,
  string,
  { rejectValue: 'cannotGetBudgetData' }
>('getBudgetSettings', async (date, { rejectWithValue }) => {
  try {
    const response = await settingsMock.getBudgetSettings(date)

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotGetBudgetSettings', type: 'error' })

    return rejectWithValue('cannotGetBudgetData')
  }
})

export const setBudgetSettings = createAsyncThunk<
  void,
  BudgetSettings,
  { rejectValue: 'cannotGetBudgetData' }
>('setBudgetSettings', async (payload, { rejectWithValue }) => {
  try {
    const response = await settingsMock.setBudgetSettings(payload)

    showToast({ messageKey: 'BudgetSettingsSet', type: 'success' })

    return response
  } catch (e: any) {
    showToast({ messageKey: 'cannotSetBudgetSettings', type: 'error' })

    return rejectWithValue('cannotGetBudgetData')
  }
})
