import { useEffect } from 'react'
import { useNotificationsSettings } from '@features/settings/hooks'
import {
  clearNotificationsSettingsState,
  getNotificationsSettings,
  selectNotificationsSettingsIsLoading,
} from '@features/settings/store/notifications'
import { Stack } from '@mui/material'
import { ScreenContent } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { NotificationsScreenSkeleton } from './NotificationsScreenSkeleton'
import { ServiceBlock } from './ServiceBlock'

export default function NotificationsScreen() {
  const translate = useTranslate('Settings.Notifications')
  const dispatch = useAppDispatch()

  const isLoading = useAppSelector(selectNotificationsSettingsIsLoading)

  const { settings, notificationsStatus, blocks, handleToggleStatus, handleChange } =
    useNotificationsSettings()

  useEffect(() => {
    dispatch(getNotificationsSettings())

    return () => {
      dispatch(clearNotificationsSettingsState())
    }
  }, [dispatch])

  return (
    <ScreenContent
      isBackButton
      title={translate('title')}
      isLoading={isLoading}
      ContentSkeleton={NotificationsScreenSkeleton}
    >
      <Stack spacing={2} maxWidth={'800px'}>
        <ServiceBlock
          title={'notificationsStatus.title'}
          options={[
            {
              title: 'notificationsStatus.subtitle',
              isChecked: notificationsStatus,
              onClick: handleToggleStatus,
            },
          ]}
        />

        {notificationsStatus && (
          <>
            <ServiceBlock
              title={'pushNotifications.title'}
              options={[
                {
                  title: 'pushNotifications.subtitle',
                  isChecked: settings.pushStatus,
                  onClick: () => handleChange(['pushStatus'], !settings.pushStatus),
                },
              ]}
            />

            {blocks.map((block) => (
              <ServiceBlock key={block.title} title={block.title} options={block.options} />
            ))}
          </>
        )}
      </Stack>
    </ScreenContent>
  )
}
