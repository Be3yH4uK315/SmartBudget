import { Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

export const WrongLink = () => {
  const translate = useTranslate('WrongLink')
  return (
    <Stack spacing={2} alignItems="center" width="100%">
      <Typography variant="h4" textAlign="center">
        {translate('incorrectLink')}
      </Typography>
      <Typography textAlign="center">{translate('incorrectLinkCaption')}</Typography>
    </Stack>
  )
}
