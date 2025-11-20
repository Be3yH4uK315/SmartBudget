import { CircularProgress, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

export function LoadingScreen() {
  const translate = useTranslate('LoadingScreen')

  return (
    <Stack
      spacing={4}
      sx={{
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'surface.main',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 100000,
      }}
    >
      <CircularProgress size={128} sx={{ alignSelf: 'center', color: 'primary.main'}} />

      <Typography variant="h4">{translate('loading')}</Typography>
    </Stack>
  )
}
