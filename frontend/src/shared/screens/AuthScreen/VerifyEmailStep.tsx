import { Button, CircularProgress, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { VerifyMode } from '@shared/types'

type Props = {
  email: string
  verifyMode: VerifyMode
  onResend: () => void
  isResending: boolean
}

export const VerifyEmailStep = ({ email, verifyMode, onResend, isResending }: Props) => {
  const translate = useTranslate('AuthScreen')

  const subtitle =
    verifyMode === 'reset'
      ? translate('verifyEmail.subtitlePassword', { email })
      : translate('verifyEmail.subtitleEmail', { email })

  return (
    <Stack spacing={2} textAlign="center">
      <Typography>{subtitle}</Typography>

      <Button variant="yellow" onClick={onResend} disabled={isResending}>
        {isResending ? <CircularProgress size={18} /> : translate('verifyEmail.buttonText')}
      </Button>
    </Stack>
  )
}
