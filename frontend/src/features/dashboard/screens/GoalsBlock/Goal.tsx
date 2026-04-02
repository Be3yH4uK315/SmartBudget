import { Stack, Typography } from '@mui/material'
import { formatCurrency } from '@shared/utils'

type Props = {
  title: string
  totalValue: number
  currentValue: number
}

export const Goal = ({ title, totalValue, currentValue }: Props) => {
  return (
    <Stack direction={'row'} spacing={2} sx={{ display: 'flex', justifyContent: 'space-between' }}>
      <Typography>{title}</Typography>

      <Typography>{`${formatCurrency(currentValue)} / ${formatCurrency(totalValue)}`}</Typography>
    </Stack>
  )
}
