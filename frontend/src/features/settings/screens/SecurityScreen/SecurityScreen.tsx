import { useEffect } from 'react'
import {
  clearSecurityState,
  deleteOtherSessions,
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
import { SessionItem } from './SessionItem'

export default function SecurityScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.Security')

  const sessions = useAppSelector(selectSessions)
  const isLoading = useAppSelector(selectIsSessionsLoading)
  const isDeleteLoading = useAppSelector(selectIsDeleteLoading)

  useEffect(() => {
    dispatch(getSessions())
  }, [dispatch])

  useEffect(() => {
    return () => {
      dispatch(clearSecurityState())
    }
  }, [])

  const handleDeleteOtherSessions = () => {
    dispatch(deleteOtherSessions())
  }

  return (
    <ScreenContent title={translate('title')} isLoading={isLoading}>
      <Stack spacing={2}>
        <ChangePasswordBlock />

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

            <Button onClick={handleDeleteOtherSessions} sx={{ color: 'error.main' }}>
              {translate('deleteOtherSessions')}
            </Button>
          </Stack>
        </StyledPaper>
      </Stack>
    </ScreenContent>
  )
}
