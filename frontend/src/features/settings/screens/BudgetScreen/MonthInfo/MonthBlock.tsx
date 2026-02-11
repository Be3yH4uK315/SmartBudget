import { BudgetSettingsStatus } from '@features/settings/types'
import { Stack, Typography } from '@mui/material'
import { StyledPaper, TooltipWithInfoIcon } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { MonthSwitch } from '.'

type Props = {
  status: BudgetSettingsStatus
}

export const MonthBlock = ({ status }: Props) => {
  const translate = useTranslate('Settings.Budget.Month')
  return (
    <StyledPaper paperSx={{ bgcolor: 'primary.main' }} elevation={0}>
      <Stack direction={'row'} justifyContent={'space-between'} alignItems={'center'}>
        <Typography variant="h4" sx={{ color: '#333' }}>
          {translate(status)}
        </Typography>

        <TooltipWithInfoIcon
          iconSx={{ color: '#333', ':hover': { color: '#333' } }}
          title={<InfoBlock status={status} />}
        />
      </Stack>
    </StyledPaper>
  )
}

const InfoBlock = ({ status }: Props) => {
  const translate = useTranslate('Settings.Budget.Tooltip')

  return (
    <Stack spacing={1} sx={{ alignItems: 'center', p: 2 }}>
      <Typography>{translate('info')}</Typography>

      <Typography variant="caption">{translate('extraInfo')}</Typography>

      <MonthSwitch status={status} />
    </Stack>
  )
}
