import React from 'react'
import { notificationsApi, notificationsMock } from '@features/notifications/api'
import { Notification } from '@features/notifications/types'
import {
  getNotificationOnClickLink,
  isTransactionCategoryChanged,
  mapNotificationMessage,
} from '@features/notifications/utils'
import { Chip, Stack, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import { openModal } from '@shared/store/modal'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router'
import { markAsRead } from '../store'

type Props = {
  notification: Notification
}
export const NotificationItem = React.memo(function NotificationItem({ notification }: Props) {
  const translate = useTranslate('Notifications')
  const translateCategories = useTranslate('Categories')
  const navigate = useNavigate()
  const dispatch = useAppDispatch()

  const color =
    notification.type === 'info'
      ? 'info.light'
      : notification.type === 'alert'
        ? 'alert.main'
        : notification.type === 'success'
          ? 'success.main'
          : notification.type === 'warning'
            ? 'error.main'
            : 'grayButton.dark'

  const handleClick = async (notification: Notification) => {
    const route = getNotificationOnClickLink(notification)

    dispatch(markAsRead(notification.id))

    if (!route && isTransactionCategoryChanged(notification)) {
      const transaction = await notificationsMock.getTransactionById(
        notification.props.transactionId,
      )

      dispatch(
        openModal({
          id: MODAL_IDS.TRANSACTION_INFO_MODAL,
          props: { transaction },
        }),
      )
    }

    if (route) {
      navigate(route)
    }
  }

  return (
    <StyledPaper
      noElevation
      paperSx={{ width: '100%', border: '2px solid', borderColor: color, cursor: 'pointer' }}
      onClick={() => handleClick(notification)}
    >
      {!notification.isRead && (
        <Chip
          component={'span'}
          label={translate('unread')}
          sx={{ width: 'max-content', height: 'auto' }}
          color="primary"
        />
      )}

      <Stack spacing={1}>
        <Stack spacing={-0.5}>
          <Typography variant="h6" sx={{ whiteSpace: 'collapse' }}>
            {translate(notification.titleKey)}
          </Typography>

          <Typography variant="caption">
            {translate('date', {
              time: dayjs(notification.date).format('HH.MM'),
              date: dayjs(notification.date).format('DD.MM.YYYY'),
            })}
          </Typography>
        </Stack>

        <Typography
          dangerouslySetInnerHTML={{
            __html: mapNotificationMessage(notification, translate, translateCategories),
          }}
        />
      </Stack>
    </StyledPaper>
  )
})
