import { NavigateNextOutlined } from '@mui/icons-material'
import { Button, CircularProgress, IconButton, Stack, TextField, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props = {
  password: string
  setPassword: (v: string) => void
  isLoading: boolean
  canSubmit: boolean
  submit: () => void
  onEnterDown: (e: React.KeyboardEvent) => void
  isMobile: boolean
  errorCode: 403 | 429 | null
  isBanned: boolean
  onForgot: () => void
}

export const PasswordStep = ({
  password,
  setPassword,
  isLoading,
  canSubmit,
  submit,
  onEnterDown,
  isMobile,
  errorCode,
  isBanned,
  onForgot,
}: Props) => {
  const translate = useTranslate('AuthScreen')

  const showWrong = errorCode === 403
  const showBan = errorCode === 429 || isBanned

  return (
    <Stack spacing={{ xs: 2, sm: 0 }} alignItems={{ xs: 'center', sm: 'normal' }}>
      <Stack direction={{ sm: 'row' }} spacing={{ xs: 2, sm: 2 }}>
        <TextField
          type="password"
          autoFocus
          label={translate('password.placeholder')}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={onEnterDown}
          sx={{ width: '100%' }}
          disabled={isLoading || showBan}
          error={showWrong || showBan}
          helperText={
            showWrong
              ? translate('password.wrongPassword')
              : showBan
                ? translate('password.tooManyAttempts')
                : undefined
          }
          FormHelperTextProps={{ sx: { color: 'error.main' } }}
        />

        <IconButton
          onClick={submit}
          disabled={!canSubmit || showBan}
          sx={{
            bgcolor: 'primary.main',
            width: { xs: 'auto', sm: 56 },
            height: { xs: 'auto', sm: 56 },
            borderRadius: 2,
            ':hover': { bgcolor: 'primary.light' },
            ':active': { bgcolor: 'primary.dark' },
            ':disabled': { bgcolor: 'grayButton.main' },
          }}
        >
          {isLoading ? (
            <CircularProgress size={24} />
          ) : (
            <>
              {isMobile && <Typography color="#333">{translate('signIn')}</Typography>}

              <NavigateNextOutlined />
            </>
          )}
        </IconButton>
      </Stack>

      <Button variant="link" onClick={onForgot} disabled={isLoading}>
        {translate('password.forgotPassword')}
      </Button>
    </Stack>
  )
}
