import { Paper, Stack, Typography } from '@mui/material'

type Props = {
  reasonTitle: string
  reasonSubtitle: string
}

export const EmptyList = ({ reasonTitle, reasonSubtitle }: Props) => {
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
        <Typography variant="h4">{reasonTitle}</Typography>

        <Typography variant="caption">{reasonSubtitle}</Typography>
      </Stack>
    </Paper>
  )
}
