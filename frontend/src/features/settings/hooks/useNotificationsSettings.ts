import { useCallback, useMemo } from 'react'
import {
  changeNotificationsStatus,
  selectNotificationsSettings,
  selectNotificationsStatus,
  updateNotificationsSettings,
} from '@features/settings/store/notifications'
import { mapSettingsToBlocks, updateByPath } from '@features/settings/utils'
import { pushApi } from '@shared/api/push'
import { selectUser, useAppDispatch, useAppSelector } from '@shared/store'

export const useNotificationsSettings = () => {
  const dispatch = useAppDispatch()

  const settings = useAppSelector(selectNotificationsSettings)
  const notificationsStatus = useAppSelector(selectNotificationsStatus)
  const userId = useAppSelector(selectUser).userId

  const handleChange = useCallback(
    async (path: string[], value: boolean) => {
      if (path[0] === 'pushStatus') {
        try {
          if (value) {
            await pushApi.enablePushNotifications(userId)
          } else {
            await pushApi.unsubscribe(userId)
          }
        } catch (e: any) {
          console.log(e)
        }
      }

      const updated = updateByPath(settings, path, value)

      dispatch(updateNotificationsSettings(updated))
    },
    [dispatch, settings, userId],
  )

  const handleToggleStatus = useCallback(() => {
    dispatch(changeNotificationsStatus(!notificationsStatus))
  }, [dispatch, notificationsStatus])

  const blocks = useMemo(
    () => mapSettingsToBlocks(settings, handleChange),
    [settings, handleChange],
  )

  return {
    settings,
    notificationsStatus,
    blocks,
    handleToggleStatus,
    handleChange,
  }
}
