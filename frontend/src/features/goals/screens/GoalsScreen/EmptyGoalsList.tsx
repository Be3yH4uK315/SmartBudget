import { Paper, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props = {
  isArchive: boolean
  filtersLength: number
}

export const EmptyGoalsList = ({ filtersLength, isArchive }: Props) => {
  const translate = useTranslate('Goals')

  const reason =
    filtersLength === 0
      ? isArchive
        ? 'NoGoals.Empty.Archive'
        : 'NoGoals.Empty'
      : isArchive
        ? 'NoGoals.Filtered.Archive'
        : 'NoGoals.Filtered'

  return (
    <Paper
      sx={{
        bgcolor: 'transparent',
        minHeight: '200px',
        textAlign: 'center',
      }}
    >
      <Stack
        spacing={1}
        sx={{
          height: '100%',
          borderStyle: 'dashed',
          borderColor: 'text.primary',
          borderWidth: '2px',
          justifyContent: 'center',
          borderRadius: '24px',
        }}
      >
        <Typography variant="h4">{translate(`${reason}.title`)}</Typography>

        <Typography variant="caption">{translate(`${reason}.subtitle`)}</Typography>
      </Stack>
    </Paper>
  )
}
