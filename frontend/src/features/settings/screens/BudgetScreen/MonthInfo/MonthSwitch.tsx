import { setBudgetStatus } from '@features/settings/store/budget'
import { BudgetSettingsStatus } from '@features/settings/types'
import { canEditNextMonthBudget } from '@features/settings/utils'
import { ToggleButton, ToggleButtonGroup } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'

type Props = {
  status: BudgetSettingsStatus
}

export const MonthSwitch = ({ status }: Props) => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.Budget.MonthSwitch')

  const toggleStatus = (value: BudgetSettingsStatus) => {
    if (!value) return

    dispatch(setBudgetStatus(value))
  }

  return (
    <ToggleButtonGroup value={status} exclusive onChange={(_, value) => toggleStatus(value)}>
      <ToggleButton value="current">{translate('current')}</ToggleButton>

      <ToggleButton value="next" disabled={!canEditNextMonthBudget()}>
        {translate('next')}
      </ToggleButton>
    </ToggleButtonGroup>
  )
}
