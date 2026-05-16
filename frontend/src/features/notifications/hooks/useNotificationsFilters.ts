import { useEffect, useRef, useState } from 'react'
import { clearNotificationsState, getNotifications } from '@features/notifications/store'
import { NotificationsFilters } from '@features/notifications/types'
import { useAppDispatch } from '@shared/store'
import { isSameFilters } from '@shared/utils'
import { useSearchParams } from 'react-router'

export function useNotificationsFilters() {
  const dispatch = useAppDispatch()

  const [searchParams, setSearchParams] = useSearchParams()

  function getInitFilters(searchParams: URLSearchParams): NotificationsFilters {
    const servicesParam = searchParams.get('services')
    const typesParam = searchParams.get('types')
    const statusesParam = searchParams.get('statuses')

    return {
      services: servicesParam ? (servicesParam.split(',') as NotificationsFilters['services']) : [],
      types: typesParam ? (typesParam.split(',') as NotificationsFilters['types']) : [],
      statuses: statusesParam ? (statusesParam as NotificationsFilters['statuses']) : '',
    }
  }

  const [localFilters, setLocalFilters] = useState<NotificationsFilters>(() =>
    getInitFilters(searchParams),
  )

  const appliedFiltersRef = useRef<NotificationsFilters>(localFilters)

  const updateLocalFilters = <K extends keyof NotificationsFilters>(
    key: K,
    value: NotificationsFilters[K],
  ) => {
    setLocalFilters((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const applyFilters = async (nextFilters: NotificationsFilters) => {
    if (isSameFilters(nextFilters, appliedFiltersRef.current)) return

    appliedFiltersRef.current = nextFilters

    dispatch(clearNotificationsState())
    dispatch(getNotifications(nextFilters))
  }

  const handleApply = () => {
    setLocalFilters(localFilters)
    applyFilters(localFilters)
  }

  const handleClearFilters = () => {
    const empty: NotificationsFilters = {
      services: [],
      types: [],
      statuses: '',
    }

    setLocalFilters(empty)
    applyFilters(empty)
  }

  const isDirty = () =>
    !isSameFilters(appliedFiltersRef.current, {
      services: [],
      types: [],
      statuses: '',
    })

  useEffect(() => {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev)

        if (localFilters.services.length) {
          params.set('services', localFilters.services.join(','))
        } else {
          params.delete('services')
        }

        if (localFilters.statuses.length) {
          params.set('statuses', localFilters.statuses)
        } else {
          params.delete('statuses')
        }

        if (localFilters.types.length) {
          params.set('types', localFilters.types.join(','))
        } else {
          params.delete('types')
        }

        return params
      },
      { replace: true },
    )
  }, [localFilters.statuses, localFilters.services, localFilters.types, setSearchParams])

  useEffect(() => {
    applyFilters(localFilters)

    return () => {
      dispatch(clearNotificationsState())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch])

  return {
    isDirty,
    appliedFiltersRef,
    localFilters,
    applyFilters,
    handleApply,
    updateLocalFilters,
    handleClearFilters,
  }
}
