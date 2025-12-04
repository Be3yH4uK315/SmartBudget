import { LinearProgress, Stack, Typography } from '@mui/material'

type Props = {
  limit: number
  categories: { value: number }[]
}

export const PercentLine = ({ limit, categories }: Props) => {
  const spent = categories.reduce((sum, c) => sum + c.value, 0)
  const percent = (spent / limit) * 100
  const overLimit = spent > limit

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
            backgroundColor: overLimit ? theme.palette.error.main : theme.palette.primary.main,
            transition: 'width 0.3s ease',
          },
        })}
      />

      <Typography sx={{ textAlign: 'right' }}>{`${Math.round(percent)} %`}</Typography>
    </Stack>
  )
}
