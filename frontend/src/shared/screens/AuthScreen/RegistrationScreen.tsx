import { useCallback, useState } from 'react'
import { Box, Button, CircularProgress, Paper, Stack, TextField, Typography } from '@mui/material'
import { authApi } from '@shared/api/auth'
import { ScreenContent } from '@shared/components/ScreenContent'
import { useTranslate, useVerifyLinkFlow } from '@shared/hooks'
import { WrongLink } from './WrongLink'

const RegistrationScreen = () => {
  const translate = useTranslate('RegistrationScreen')
  const { email, token, isVerifying, verified, isSubmitting, wrapSubmit } = useVerifyLinkFlow()

  const [name, setName] = useState('')
  const [country, setCountry] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  const mismatch = confirmPassword && confirmPassword !== password
  const canSubmit =
    verified && !isSubmitting && name && country && password && confirmPassword && !mismatch

  const onSubmit = useCallback(
    (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault()
      if (!canSubmit) return

      wrapSubmit(() =>
        authApi.completeRegistration({
          email,
          token,
          password,
          name,
          country,
        }),
      )
    },
    [canSubmit, wrapSubmit, email, token, password, name, country],
  )

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
          {verified && (
            <Typography variant="h3" textAlign="center">
              {translate('title')}
            </Typography>
          )}

          {isVerifying ? (
            <Stack alignItems="center" justifyContent="center" width="100%" py={6}>
              <CircularProgress size={60} />
            </Stack>
          ) : verified === false ? (
            <WrongLink />
          ) : (
            <Box component="form" onSubmit={onSubmit} sx={{ width: '100%' }}>
              <Stack spacing={2} width="100%">
                <TextField
                  label={translate('name')}
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isSubmitting}
                  fullWidth
                />

                {/** TODO: список стран */}
                <TextField
                  label={translate('country')}
                  autoComplete="country-name"
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  disabled={isSubmitting}
                  fullWidth
                />

                <TextField
                  label={translate('password')}
                  type="password"
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isSubmitting}
                  fullWidth
                />

                <TextField
                  label={translate('repeatPassword')}
                  type="password"
                  autoComplete="new-password"
                  value={confirmPassword}
                  error={!!mismatch}
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

                <Typography textAlign="center" sx={{ fontSize: 14, mt: 1, px: 2 }}>
                  {translate('caption')}
                </Typography>
              </Stack>
            </Box>
          )}
        </Stack>
      </Paper>
    </ScreenContent>
  )
}

export default RegistrationScreen
