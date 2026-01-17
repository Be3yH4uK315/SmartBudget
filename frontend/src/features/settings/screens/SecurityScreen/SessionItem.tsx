import React from 'react'
import { deleteSession } from '@features/settings/store/security'
import { Session } from '@features/settings/types'
import { Box, Button, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import dayjs from 'dayjs'

type Props = {
  session: Session
  isLoading: boolean
}

export const SessionItem = React.memo(({ session, isLoading }: Props) => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.Security.Sessions')

  const date = dayjs(session.lastActivity).format('DD MMMM YYYY')
  const time = dayjs(session.lastActivity).format('HH:mm').split(' ')

  const title = [session.deviceName, session.location, session.ip].join(', ')
  const lastActivity = translate('lastActivity', {
    date: date,
    time: time,
  })

  const handleDeleteSession = () => {
    dispatch(deleteSession(session.sessionId))
  }

  return (
    <Stack
      sx={{
        display: 'flex',
        width: '100%',
        justifyContent: 'space-between',
        alignItems: 'center',
        bgcolor: 'surface.main',
        borderRadius: '12px',
        px: 2,
        py: 1,
        whiteSpace: 'wrap',
      }}
      direction={{ xs: 'column', sm: 'row' }}
      spacing={2}
    >
      <Stack>
        <Typography>{title}</Typography>

        <Typography variant="caption">{lastActivity}</Typography>
      </Stack>

      {session.isCurrent && (
        <Box
          sx={{
            display: 'flex',
            px: 2,
            py: 0.5,
            bgcolor: 'primary.main',
            borderRadius: '12px',
            textAlign: 'center',
          }}
        >
          <Typography variant="caption" sx={{ color: '#333' }}>
            {translate('current')}
          </Typography>
        </Box>
      )}

      {!session.isCurrent && (
        <Button
          disabled={isLoading}
          sx={{ height: 'min-content', color: 'error.main', '&:hover': { color: 'error.dark' } }}
          onClick={handleDeleteSession}
        >
          {translate('deleteSession')}
        </Button>
      )}
    </Stack>
  )
})
