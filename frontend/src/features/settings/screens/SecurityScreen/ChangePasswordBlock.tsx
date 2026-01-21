import { useChangePasswordForm } from '@features/settings/hooks'
import { selectIsPasswordChanging } from '@features/settings/store/security'
import { Button, CircularProgress, Stack, TextField, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { logoutHelper } from '@shared/utils'

export const ChangePasswordBlock = () => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.Security.ChangePassword')

  const isPasswordChanging = useAppSelector(selectIsPasswordChanging)

  const { values, errors, shouldShowError, handleChange, handleSubmit, handleBlur } =
    useChangePasswordForm()

  const handleForgotPassword = () => {
    logoutHelper(dispatch)
  }

  return (
    <StyledPaper elevation={0}>
      <Stack spacing={2}>
        <Typography variant="h4">{translate('title')}</Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2} width={'100%'}>
            <TextField
              type="text"
              label={translate('oldPassword')}
              value={values.password}
              onChange={handleChange('password')}
              required
            />

            <TextField
              type="text"
              label={translate('newPassword')}
              value={values.newPassword}
              onChange={handleChange('newPassword')}
              onBlur={handleBlur('newPassword')}
              error={shouldShowError('newPassword')}
              helperText={shouldShowError('newPassword') ? errors().newPassword : ''}
              slotProps={{ htmlInput: { minLength: 8 } }}
              required
            />

            <TextField
              type="text"
              label={translate('newPasswordConfirm')}
              value={values.newPasswordConfirm}
              onChange={handleChange('newPasswordConfirm')}
              onBlur={handleBlur('newPasswordConfirm')}
              error={shouldShowError('newPasswordConfirm')}
              helperText={shouldShowError('newPasswordConfirm') ? errors().newPasswordConfirm : ''}
              slotProps={{ htmlInput: { minLength: 8 } }}
              required
            />

            <Stack spacing={1}>
              <Typography
                variant="caption"
                sx={{ color: 'secondary.main', cursor: 'pointer', width: 'max-content' }}
                onClick={handleForgotPassword}
              >
                {translate('forgotPassword')}
              </Typography>

              <Button variant="yellow" type="submit" disabled={isPasswordChanging}>
                {isPasswordChanging ? (
                  <CircularProgress size={20} sx={{ color: '#333' }} />
                ) : (
                  translate('button')
                )}
              </Button>
            </Stack>
          </Stack>
        </form>
      </Stack>
    </StyledPaper>
  )
}
