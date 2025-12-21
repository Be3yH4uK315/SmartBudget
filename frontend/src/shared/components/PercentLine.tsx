import { LinearProgress, Stack, Typography, useTheme } from '@mui/material'
import { formatPercent } from '@shared/utils'

type Props = {
  limit: number
  currentValue: number
}

export const PercentLine = ({ limit, currentValue }: Props) => {
  const theme = useTheme()

  const percent = (currentValue / limit) * 100
  const overLimit = currentValue > limit
  const preOverLimit = currentValue / limit >= 0.8

  const lineColor = overLimit
    ? theme.palette.error.main
    : preOverLimit
      ? theme.palette.primary.main
      : theme.palette.success.main

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      <LinearProgress
        variant="determinate"
        value={percent > 100 ? 100 : percent}
        sx={(theme) => ({
          flex: 1,
          height: 12,
          borderRadius: 6,

          '&.MuiLinearProgress-root': {
            backgroundColor: theme.palette.grey[300],
          },
          '& .MuiLinearProgress-bar': {
            borderRadius: 6,
            backgroundColor: lineColor,
            transition: 'width 0.3s ease',
          },
        })}
      />

      <Typography>{formatPercent(percent / 100)}</Typography>
    </Stack>
  )
}
