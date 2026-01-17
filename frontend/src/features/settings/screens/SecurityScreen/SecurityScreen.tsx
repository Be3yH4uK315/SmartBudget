import { useEffect } from 'react'
import {
  clearSecurityState,
  deleteOtherSessions,
  getRefreshTokenDuration,
  getSessions,
  selectIsDeleteLoading,
  selectIsSessionsLoading,
  selectSessions,
} from '@features/settings/store/security'
import { Button, Stack, Typography } from '@mui/material'
import { ScreenContent, StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { ChangePasswordBlock } from './ChangePasswordBlock'
import { RefreshTokenDurationBlock } from './RefreshTokenDurationBlock'
import { SecurityScreenSkeleton } from './SecurityScreenSkeleton'
import { SessionItem } from './SessionItem'

export default function SecurityScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.Security')

  const sessions = useAppSelector(selectSessions)
  const isLoading = useAppSelector(selectIsSessionsLoading)
  const isDeleteLoading = useAppSelector(selectIsDeleteLoading)

  useEffect(() => {
    dispatch(getSessions())
    dispatch(getRefreshTokenDuration())
  }, [dispatch])

  useEffect(() => {
    return () => {
      dispatch(clearSecurityState())
    }
  }, [dispatch])

  const handleDeleteOtherSessions = () => {
    dispatch(deleteOtherSessions())
  }

  return (
    <ScreenContent
      title={translate('title')}
      isLoading={isLoading}
      ContentSkeleton={SecurityScreenSkeleton}
      isBackButton
    >
      <Stack spacing={2} sx={{ maxWidth: { xs: '100%', md: '70%' } }}>
        <ChangePasswordBlock />

        <RefreshTokenDurationBlock />

        {sessions.length > 0 && (
          <StyledPaper paperSx={{ gap: 2 }} elevation={0}>
            <Typography variant="h4">{translate('Sessions.title')}</Typography>

            <Stack spacing={2}>
              {sessions.map((session) => {
                return (
                  <SessionItem
                    key={session.sessionId}
                    session={session}
                    isLoading={isDeleteLoading}
                  />
                )
              })}

              {sessions.length > 1 && (
                <Button
                  onClick={handleDeleteOtherSessions}
                  sx={{
                    color: 'error.main',
                    bgcolor: 'surface.main',
                    '&:hover': { color: 'error.dark' },
                  }}
                >
                  {translate('deleteOtherSessions')}
                </Button>
              )}
            </Stack>
          </StyledPaper>
        )}
      </Stack>
    </ScreenContent>
  )
}
