import { useChangePasswordFrom } from '@features/settings/hooks/useChangePasswordForm'
import { selectIsPasswordChanging } from '@features/settings/store/security'
import { Button, Stack, TextField, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { logoutHelper } from '@shared/utils'

export const ChangePasswordBlock = () => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.Security.ChangePassword')

  const isPasswordChanging = useAppSelector(selectIsPasswordChanging)

  const { values, errors, shouldShowError, handleChange, canSubmit, handleSubmit } =
    useChangePasswordFrom()

  const isDisabled = !canSubmit || isPasswordChanging

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
              error={shouldShowError('password')}
            />

            <TextField
              type="text"
              label={translate('newPassword')}
              value={values.newPassword}
              onChange={handleChange('newPassword')}
              error={shouldShowError('newPassword')}
              helperText={shouldShowError('newPassword') ? errors.newPassword : ''}
            />

            <TextField
              type="text"
              label={translate('newPasswordConfirm')}
              value={values.newPasswordConfirm}
              onChange={handleChange('newPasswordConfirm')}
              error={shouldShowError('newPasswordConfirm')}
              helperText={shouldShowError('newPasswordConfirm') ? errors.newPasswordConfirm : ''}
            />

            <Stack spacing={1}>
              <Typography
                variant="caption"
                sx={{ color: 'secondary.main', cursor: 'pointer', width: 'max-content' }}
                onClick={handleForgotPassword}
              >
                {translate('forgotPassword')}
              </Typography>

              <Button disabled={isDisabled} variant="yellow" type="submit">
                {translate('button')}
              </Button>
            </Stack>
          </Stack>
        </form>
      </Stack>
    </StyledPaper>
  )
}
