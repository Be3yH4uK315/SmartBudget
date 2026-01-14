import { Stack, Typography } from '@mui/material'
import { formatCurrency } from '@shared/utils/formatCurrency'

type Props = {
  title: string
  targetValue: number
  currentValue: number
}

export const Goal = ({ title, targetValue, currentValue }: Props) => {
  return (
    <Stack direction={'row'} spacing={2} sx={{ display: 'flex', justifyContent: 'space-between' }}>
      <Typography>{title}</Typography>

      <Typography>{formatCurrency(currentValue) + '/' + formatCurrency(targetValue)}</Typography>
    </Stack>
  )
}
