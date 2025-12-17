import { NavigateNextOutlined } from '@mui/icons-material'
import { CircularProgress, IconButton, Stack, TextField, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props = {
  email: string
  setEmail: (v: string) => void
  isLoading: boolean
  canSubmit: boolean
  submit: () => void
  onEnterDown: (e: React.KeyboardEvent) => void
  isMobile: boolean
}

export const EmailStep = ({
  email,
  setEmail,
  isLoading,
  canSubmit,
  submit,
  onEnterDown,
  isMobile,
}: Props) => {
  const translate = useTranslate('AuthScreen')
  return (
    <Stack direction={{ sm: 'row' }} spacing={{ xs: 2, sm: 2 }}>
      <TextField
        type="email"
        inputMode="email"
        autoFocus
        label={translate('email.placeholder')}
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        onKeyDown={onEnterDown}
        sx={{ width: '100%' }}
        disabled={isLoading}
      />

      <IconButton
        onClick={submit}
        disabled={!canSubmit}
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
  )
}
