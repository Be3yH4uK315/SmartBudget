import { useEffect } from 'react'
import {
  clearBudgetSettingsState,
  getBudgetSettings,
  selectBudgetSettings,
  selectIsBudgetSettingsLoading,
  selectIsBudgetSettingsUpdating,
  setBudgetSettings,
} from '@features/settings/store/budget'
import { mapBudgetSettingsToForm } from '@features/settings/utils'
import { Button, CircularProgress, Stack } from '@mui/material'
import { BudgetForm, ScreenContent } from '@shared/components'
import { useBudgetForm, useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { mapFormToBudgetPayload } from '@shared/utils'
import dayjs from 'dayjs'
import { BudgetScreenSkeleton } from './BudgetScreenSkeleton'

export default function BudgetScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.Budget')

  const isUpdating = useAppSelector(selectIsBudgetSettingsUpdating)
  const isLoading = useAppSelector(selectIsBudgetSettingsLoading)
  const settings = useAppSelector(selectBudgetSettings)

  const props = useBudgetForm()

  useEffect(() => {
    dispatch(getBudgetSettings(dayjs().format('YYYY-MM-DD')))

    return () => {
      dispatch(clearBudgetSettingsState())
    }
  }, [dispatch])

  useEffect(() => {
    if (settings) {
      props.resetInitValues(mapBudgetSettingsToForm(settings))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const payload = mapFormToBudgetPayload(props.values)
    dispatch(setBudgetSettings(payload))
  }

  return (
    <ScreenContent title={translate('title')} isBackButton>
      {isLoading ? (
        <BudgetScreenSkeleton />
      ) : (
        <Stack maxWidth={'800px'}>
          <form onSubmit={handleSubmit}>
            <Stack spacing={2} maxWidth="800px">
              <BudgetForm {...props} />

              {props.canSubmit() && (
                <Button type="submit" variant="yellow" disabled={isUpdating}>
                  {isUpdating ? (
                    <CircularProgress size={20} sx={{ color: '#333' }} />
                  ) : (
                    translate('submitButton')
                  )}
                </Button>
              )}
            </Stack>
          </form>
        </Stack>
      )}
    </ScreenContent>
  )
}
