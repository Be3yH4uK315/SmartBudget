import { useCallback, useMemo } from 'react'
import {
  changeNotificationsStatus,
  selectNotificationsSettings,
  selectNotificationsStatus,
  updateNotificationsSettings,
} from '@features/settings/store/notifications'
import { mapSettingsToBlocks, updateByPath } from '@features/settings/utils'
import { useAppDispatch, useAppSelector } from '@shared/store'

export const useNotificationsSettings = () => {
  const dispatch = useAppDispatch()

  const settings = useAppSelector(selectNotificationsSettings)
  const notificationsStatus = useAppSelector(selectNotificationsStatus)

  const handleChange = useCallback(
    (path: string[], value: boolean) => {
      const updated = updateByPath(settings, path, value)
      dispatch(updateNotificationsSettings(updated))
    },
    [dispatch, settings],
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
