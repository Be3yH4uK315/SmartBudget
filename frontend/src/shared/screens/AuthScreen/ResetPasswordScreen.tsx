import { useMemo, useState } from 'react'
import { Button, CircularProgress, Paper, Stack, TextField, Typography } from '@mui/material'
import { auth_mock } from '@shared/api/auth'
import { ScreenContent } from '@shared/components/ScreenContent'
import { useTranslate, useVerifyLinkFlow } from '@shared/hooks'
import { WrongLink } from './WrongLink'

export const ResetPasswordScreen = () => {
  const translate = useTranslate('ResetPasswordScreen')
  const { email, token, isVerifying, verified, isSubmitting, wrapSubmit } = useVerifyLinkFlow()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const mismatch = confirmPassword.length > 0 && confirmPassword !== password

  const canSubmit = useMemo(() => {
    if (!verified || isSubmitting) return false
    return password.trim() && confirmPassword.trim() && !mismatch
  }, [verified, isSubmitting, password, confirmPassword, mismatch])

  const onSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!canSubmit) return

    wrapSubmit(() =>
      auth_mock.completeReset({
        email,
        token,
        new_password: password,
      }),
    )
  }

  return (
    <ScreenContent containerSx={{ justifyContent: 'center', alignItems: 'center' }} noScrollButton>
      <Paper
        elevation={3}
        sx={{
          bgcolor: 'surface.light',
          pt: 6,
          pb: 8,
          px: { xs: 4, sm: 8, md: 12 },
          display: 'flex',
          position: 'relative',
          maxWidth: 600,
          width: '100%',
          justifyContent: 'center',
          borderRadius: 3,
        }}
      >
        <Stack width="100%" spacing={4} alignItems="center">
          <Typography variant="h3" textAlign="center">
            {translate('title')}
          </Typography>

          {isVerifying ? (
            <Stack alignItems="center" justifyContent="center" width="100%" py={6}>
              <CircularProgress size={60} />
            </Stack>
          ) : verified === false ? (
            <WrongLink />
          ) : (
            <form style={{ width: '100%' }} onSubmit={onSubmit}>
              <Stack spacing={2} width="100%">
                <TextField
                  label={translate('password')}
                  type="password"
                  value={password}
                  autoComplete="new-password"
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting}
                  fullWidth
                  autoFocus
                />

                <TextField
                  label={translate('repeatPassword')}
                  type="password"
                  value={confirmPassword}
                  autoComplete="new-password"
                  error={mismatch}
                  helperText={mismatch ? translate('passwordsNotMatch') : ''}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={isSubmitting}
                  fullWidth
                />

                <Button
                  type="submit"
                  variant="yellow"
                  disabled={!canSubmit}
                  sx={{ width: '100%', height: 48, borderRadius: 2 }}
                  startIcon={isSubmitting ? <CircularProgress size={16} /> : null}
                >
                  {translate('continue')}
                </Button>
              </Stack>
            </form>
          )}
        </Stack>
      </Paper>
    </ScreenContent>
  )
}
