import { NotificationsFilters } from '@features/notifications/types'
import { useTranslate } from '@shared/hooks'

type NotificationsChip =
  | { type: 'services'; value: string }
  | { type: 'statuses'; value: string }
  | { type: 'types'; value: string }

type Props = {
  localFilters: NotificationsFilters
  applyFilters: (value: NotificationsFilters) => void
  updateLocalFilters: <K extends keyof NotificationsFilters>(
    key: K,
    value: NotificationsFilters[K],
  ) => void
}

export function useNotificationsChips({ localFilters, updateLocalFilters, applyFilters }: Props) {
  const translate = useTranslate('Notifications.Filters')

  const chips: NotificationsChip[] = []

  localFilters.services.forEach((services) => chips.push({ type: 'services', value: services }))

  if (localFilters.statuses) chips.push({ type: 'statuses', value: localFilters.statuses })

  localFilters.types.forEach((priority) => chips.push({ type: 'types', value: priority }))

  const getLabel = (chip: NotificationsChip) => {
    switch (chip.type) {
      case 'services':
        return translate(chip.value)

      case 'statuses':
        return translate(`Statuses.${chip.value}`)

      case 'types':
        return translate(chip.value)
    }
  }

  const handleDeleteChip = (chip: NotificationsChip) => {
    switch (chip.type) {
      case 'services': {
        const next = {
          ...localFilters,
          services: localFilters.services.filter((t) => t !== chip.value),
        }
        updateLocalFilters('services', next.services)
        applyFilters(next)
        break
      }

      case 'statuses': {
        const next = {
          ...localFilters,
          statuses: '' as const,
        }
        updateLocalFilters('statuses', next.statuses)
        applyFilters(next)
        break
      }

      case 'types': {
        const next = {
          ...localFilters,
          types: localFilters.types.filter((p) => p !== chip.value),
        }
        updateLocalFilters('types', next.types)
        applyFilters(next)
        break
      }
    }
  }

  return { chips, getLabel, handleDeleteChip }
}
