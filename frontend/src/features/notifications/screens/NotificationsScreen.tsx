import { useEffect } from 'react'
import { NotificationsList } from '@features/notifications/components'
import {
  clearNotificationsState,
  getNotifications,
  markAllAsRead,
  selectIsLastNotification,
  selectIsNotificationsLoading,
  selectNotifications,
} from '@features/notifications/store'
import { Button, Stack } from '@mui/material'
import { EmptyList, ScreenContent } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { NotificationsScreenSkeleton } from './NotificationsScreenSkeleton'

export default function NotificationsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Notifications')

  const isLoading = useAppSelector(selectIsNotificationsLoading)
  const isLast = useAppSelector(selectIsLastNotification)
  const notifications = useAppSelector(selectNotifications)

  useEffect(() => {
    dispatch(getNotifications())

    return () => {
      dispatch(clearNotificationsState())
    }
  }, [dispatch])

  return (
    <ScreenContent title={translate('title')}>
      <Stack spacing={1} maxWidth={'800px'}>
        {notifications.length === 0 && !isLoading && (
          <EmptyList
            reasonTitle={translate('noTransactions')}
            reasonSubtitle={translate('noTransactionsSubtitle')}
          />
        )}

        <Stack direction={'row'} sx={{ width: '100%', justifyContent: 'end', display: 'flex' }}>
          <Button
            variant="yellow"
            sx={{ height: 'max-content' }}
            onClick={() => dispatch(markAllAsRead())}
          >
            {translate('markAllAsRead')}
          </Button>
        </Stack>

        {notifications.length > 0 && (
          <NotificationsList isLast={isLast} isLoading={isLoading} notifications={notifications} />
        )}

        {notifications.length === 0 && isLoading && <NotificationsScreenSkeleton />}
      </Stack>
    </ScreenContent>
  )
}
