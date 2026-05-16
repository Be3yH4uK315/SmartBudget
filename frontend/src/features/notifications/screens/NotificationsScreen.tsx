import { NotificationsFiltersBlock, NotificationsList } from '@features/notifications/components'
import { useNotificationsFilters } from '@features/notifications/hooks'
import {
  markAllAsRead,
  selectIsLastNotification,
  selectIsNotificationsLoading,
  selectNotifications,
  selectUnreadCount,
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
  const unreadCount = useAppSelector(selectUnreadCount)

  const { isDirty, appliedFiltersRef, ...props } = useNotificationsFilters()

  const translationKey = isDirty() ? 'NoNotifications.Filtered' : 'NoNotifications.Empty'

  const emptyListReason = {
    title: translate(`${translationKey}.title`),
    subtitle: translate(`${translationKey}.subtitle`),
  }

  return (
    <ScreenContent title={translate('title')}>
      <Stack spacing={2} maxWidth={'800px'}>
        {notifications.length === 0 && !isLoading && (
          <EmptyList
            reasonTitle={emptyListReason.title}
            reasonSubtitle={emptyListReason.subtitle}
          />
        )}

        <Stack spacing={2} direction={'column'} sx={{ display: 'flex' }}>
          {unreadCount > 0 && (
            <Button
              variant="yellow"
              sx={{ height: 'max-content' }}
              onClick={() => dispatch(markAllAsRead())}
            >
              {translate('markAllAsRead')}
            </Button>
          )}

          {notifications.length > 0 && <NotificationsFiltersBlock isDirty={isDirty()} {...props} />}
        </Stack>

        {notifications.length > 0 && (
          <NotificationsList
            isLast={isLast}
            isLoading={isLoading}
            notifications={notifications}
            appliedFiltersRef={appliedFiltersRef}
          />
        )}

        {notifications.length === 0 && isLoading && <NotificationsScreenSkeleton />}
      </Stack>
    </ScreenContent>
  )
}
