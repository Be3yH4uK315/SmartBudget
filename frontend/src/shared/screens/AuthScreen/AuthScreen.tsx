import { ArrowBackOutlined } from '@mui/icons-material'
import { IconButton, Paper, Stack, Typography, useMediaQuery, useTheme } from '@mui/material'
import { useAuthFlow, useTranslate } from '@shared/hooks'
import { ScreenContent } from 'src/shared/components/ScreenContent'
import { EmailStep } from './EmailStep'
import { PasswordStep } from './PasswordStep'
import { VerifyEmailStep } from './VerifyEmailStep'

const AuthScreen = () => {
  const translate = useTranslate('AuthScreen')
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  const {
    step,
    email,
    password,
    isLoading,
    canSubmit,
    normalizedEmail,
    errorCode,
    isBanned,
    verifyMode,
    isResending,
    setEmail,
    setPassword,
    submit,
    onKeyDown,
    resetPasswordFlow,
    resendVerifyEmail,
    goBack,
  } = useAuthFlow()

  const title = translate(`${step}.title`)
  const subtitle = step === 'email' ? translate('email.subtitle') : null

  return (
    <ScreenContent containerSx={{ justifyContent: 'center', alignItems: 'center' }}>
      <Paper
        elevation={3}
        sx={{
          bgcolor: 'surface.light',
          pt: 6,
          pb: 8,
          px: 12,
          display: 'flex',
          position: 'relative',
          maxWidth: 600,
          width: '100%',
          justifyContent: 'center',
          borderRadius: 3,
        }}
      >
        <IconButton
          onClick={goBack}
          disabled={isLoading}
          aria-label="Назад"
          sx={{
            position: 'absolute',
            top: 20,
            left: 20,
            visibility: step === 'email' ? 'hidden' : 'visible',
            zIndex: 2,
          }}
        >
          <ArrowBackOutlined />
        </IconButton>

        <Stack spacing={4} width="100%">
          <Stack alignItems="center">
            <Typography variant="h3">{title}</Typography>

            {subtitle && <Typography textAlign="center">{subtitle}</Typography>}
          </Stack>

          {step === 'email' && (
            <EmailStep
              email={email}
              setEmail={setEmail}
              isLoading={isLoading}
              canSubmit={canSubmit}
              submit={submit}
              onEnterDown={onKeyDown}
              isMobile={isMobile}
            />
          )}

          {step === 'password' && (
            <PasswordStep
              password={password}
              setPassword={setPassword}
              isLoading={isLoading}
              canSubmit={canSubmit}
              submit={submit}
              onEnterDown={onKeyDown}
              isMobile={isMobile}
              errorCode={errorCode}
              isBanned={isBanned}
              onForgot={resetPasswordFlow}
            />
          )}

          {step === 'verifyEmail' && (
            <VerifyEmailStep
              email={normalizedEmail}
              verifyMode={verifyMode}
              onResend={resendVerifyEmail}
              isResending={isResending}
            />
          )}
        </Stack>
      </Paper>
    </ScreenContent>
  )
}

export default AuthScreen
