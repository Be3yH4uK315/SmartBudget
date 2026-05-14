import { NOTIFICATIONS_SERVICES, NOTIFICATIONS_TYPES } from '@features/notifications/constants'
import { useNotificationsChips } from '@features/notifications/hooks'
import {
  NotificationService,
  NotificationsFilters,
  NotificationStatus,
  NotificationType,
} from '@features/notifications/types'
import { Button, Chip, Stack } from '@mui/material'
import { FiltersSelect, StyledBox } from '@shared/components'
import { useTranslate } from '@shared/hooks'

type LocalNotificationService = Exclude<NotificationService, 'Limit'>

type Props = {
  isDirty: boolean
  localFilters: NotificationsFilters
  handleClearFilters: () => void
  handleApply: () => void
  applyFilters: (value: any) => void
  updateLocalFilters: <K extends keyof NotificationsFilters>(
    key: K,
    value: NotificationsFilters[K],
  ) => void
}

export const NotificationsFiltersBlock = ({ ...props }: Props) => {
  const translate = useTranslate('Notifications.Filters')

  const {
    handleClearFilters,
    handleApply,
    isDirty,
    localFilters,
    updateLocalFilters,
    applyFilters,
  } = props

  const { chips, getLabel, handleDeleteChip } = useNotificationsChips(props)

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between' }}>
        <Stack spacing={2} direction={'row'}>
          <FiltersSelect<NotificationStatus | ''>
            value={localFilters.statuses}
            items={['', 'read', 'unread']}
            translateItemKey={'Notifications.Filters.Statuses'}
            translateKey={'Notifications.Filters'}
            placeholderKey={'placeholder.statuses'}
            onChange={(e) => {
              const next = { ...localFilters, statuses: e.target.value }
              updateLocalFilters('statuses', next.statuses)
              applyFilters(next)
            }}
            formSx={{ width: { xs: '100%', sm: 'auto' } }}
          />

          <FiltersSelect<NotificationType>
            multiple
            value={localFilters.types}
            items={NOTIFICATIONS_TYPES}
            translateItemKey={'Notifications.Filters'}
            translateKey={'Notifications.Filters'}
            placeholderKey={'placeholder.types'}
            onChange={(e) => updateLocalFilters('types', e.target.value)}
            onClose={handleApply}
          />

          <FiltersSelect<LocalNotificationService>
            multiple
            value={localFilters.services}
            items={NOTIFICATIONS_SERVICES}
            translateItemKey={'Notifications.Filters'}
            translateKey={'Notifications.Filters'}
            placeholderKey={'placeholder.services'}
            onChange={(e) => updateLocalFilters('services', e.target.value)}
            onClose={handleApply}
          />
        </Stack>

        {(localFilters.statuses?.length > 0 ||
          localFilters.types?.length > 0 ||
          localFilters.services?.length > 0) && (
          <Button onClick={handleClearFilters} sx={{ height: 'min-content' }} variant="yellow">
            {translate('clear')}
          </Button>
        )}
      </Stack>

      {isDirty && (
        <StyledBox>
          {chips.map((chip, i) => (
            <Chip
              key={i}
              label={getLabel(chip)}
              onDelete={() => handleDeleteChip(chip)}
              sx={{
                bgcolor: 'primary.main',
                color: '#333',
                typography: 'caption',
                '& .MuiSvgIcon-root': { color: '#333' },
              }}
            />
          ))}
        </StyledBox>
      )}
    </Stack>
  )
}
