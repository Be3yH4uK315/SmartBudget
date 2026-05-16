import { useEffect, useRef, useState } from 'react'
import { clearGoalsState, getGoals } from '@features/goals/store/goals'
import { GoalsFilters } from '@features/goals/types'
import { ROUTES } from '@shared/constants/routes'
import { useAppDispatch } from '@shared/store'
import { isSameFilters } from '@shared/utils'
import { useMatch, useSearchParams } from 'react-router'

export function useGoalsFilters() {
  const dispatch = useAppDispatch()

  const [searchParams, setSearchParams] = useSearchParams()
  const isArchivePage = !!useMatch(ROUTES.PAGES.GOALS.ARCHIVE)

  function getInitFilters(searchParams: URLSearchParams): GoalsFilters {
    const tagsParam = searchParams.get('tags')
    const priorityParam = searchParams.get('priority')

    return {
      tags: tagsParam ? (tagsParam.split(',') as GoalsFilters['tags']) : [],
      priority: priorityParam ? (priorityParam.split(',') as GoalsFilters['priority']) : [],
      isArchived: isArchivePage,
    }
  }

  const [localFilters, setLocalFilters] = useState<GoalsFilters>(() => getInitFilters(searchParams))

  const appliedFiltersRef = useRef<GoalsFilters>(localFilters)

  const updateLocalFilters = <K extends keyof GoalsFilters>(key: K, value: GoalsFilters[K]) => {
    setLocalFilters((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const applyFilters = async (nextFilters: GoalsFilters) => {
    if (isSameFilters(nextFilters, appliedFiltersRef.current)) return

    appliedFiltersRef.current = nextFilters

    dispatch(getGoals(nextFilters))
  }

  const handleApply = () => {
    const next = {
      ...localFilters,
      isArchived: isArchivePage,
    }

    setLocalFilters(next)
    applyFilters(next)
  }

  const handleClearFilters = () => {
    const empty: GoalsFilters = {
      tags: [],
      priority: [],
      isArchived: isArchivePage,
    }

    setLocalFilters(empty)
    applyFilters(empty)
  }

  const isDirty = () =>
    !isSameFilters(appliedFiltersRef.current, {
      tags: [],
      priority: [],
      isArchived: isArchivePage,
    })

  useEffect(() => {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev)

        if (localFilters.tags.length) {
          params.set('tags', localFilters.tags.join(','))
        } else {
          params.delete('tags')
        }

        if (localFilters.priority.length) {
          params.set('priority', localFilters.priority.join(','))
        } else {
          params.delete('priority')
        }

        return params
      },
      { replace: true },
    )
  }, [localFilters.tags, localFilters.priority, setSearchParams])

  useEffect(() => {
    applyFilters({
      ...localFilters,
      isArchived: isArchivePage,
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isArchivePage])

  useEffect(() => {
    dispatch(getGoals(localFilters))

    return () => {
      dispatch(clearGoalsState())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch])

  return {
    isDirty,
    isArchivePage,
    appliedFiltersRef,
    localFilters,
    applyFilters,
    handleApply,
    updateLocalFilters,
    handleClearFilters,
  }
}
