import { useCallback, useMemo } from 'react'
import 'dayjs/locale/ru'
import { getNotifications } from '@features/notifications/store'
import { NotificationsBlock, NotificationsFilters } from '@features/notifications/types'
import { Typography } from '@mui/material'
import { ListFooter, MUIComponents } from '@shared/components/GroupedVirtuoso'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import { normalizeBlocks } from '@shared/utils'
import dayjs from 'dayjs'
import { GroupedVirtuoso } from 'react-virtuoso'
import { NotificationItem } from './NotificationItem'

type Props = {
  isLast: boolean
  isLoading: boolean
  notifications: NotificationsBlock[]
  appliedFiltersRef: React.RefObject<NotificationsFilters>
}

export const NotificationsList = ({
  isLast,
  isLoading,
  notifications,
  appliedFiltersRef,
}: Props) => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('ListDate')

  const normalizedBlocks = useMemo(() => normalizeBlocks(notifications), [notifications])

  const loadMore = useCallback(() => {
    dispatch(getNotifications(appliedFiltersRef.current))
  }, [dispatch, appliedFiltersRef])

  const formatGroupDate = (inputDate: string) => {
    const date = dayjs.utc(inputDate).local()

    if (date.isSame(dayjs(), 'day')) return translate('today')
    if (date.isSame(dayjs().subtract(1, 'day'), 'day')) return translate('yesterday')

    return date.format('D MMMM')
  }

  return (
    <GroupedVirtuoso
      style={{ height: '100vh' }}
      defaultItemHeight={65}
      components={{
        ...MUIComponents,
        Footer: () => <ListFooter isLast={isLast} isLoading={isLoading} />,
      }}
      increaseViewportBy={{ bottom: 400, top: 0 }}
      useWindowScroll
      overscan={200}
      groupCounts={normalizedBlocks.groupCounts}
      endReached={() => (!isLoading && !isLast ? loadMore() : null)}
      groupContent={(index) => (
        <Typography variant="h4">{formatGroupDate(normalizedBlocks.groups[index])}</Typography>
      )}
      itemContent={(index) => <NotificationItem notification={normalizedBlocks.items[index]} />}
    />
  )
}
