import { useState } from 'react'
import { getGoals, resetFilters, setTags } from '@features/goals/store/goals'
import { FiltersTag, GoalsFilters } from '@features/goals/types'
import { SelectChangeEvent } from '@mui/material'
import { useAppDispatch } from '@shared/store'

export function useGoalsFilters(filters: GoalsFilters) {
  const dispatch = useAppDispatch()

  const [localTags, setLocalTags] = useState<FiltersTag[]>(filters.tags)

  const handleTagsChange = (e: SelectChangeEvent<FiltersTag[]>) => {
    const value = e.target.value
    setLocalTags(typeof value === 'string' ? (value.split(',') as FiltersTag[]) : value)
  }

  const handleApplyTags = () => {
    if (localTags === filters.tags) return

    dispatch(setTags(localTags))
    dispatch(getGoals())
  }

  const handleRemoveTag = (tag: FiltersTag) => {
    const next = localTags.filter((t) => t !== tag)

    setLocalTags(next)
    dispatch(setTags(next))
    dispatch(getGoals())
  }

  const handleClearFilters = () => {
    if (filters.tags?.length === 0) return

    setLocalTags([])

    dispatch(resetFilters())
    dispatch(getGoals())
  }

  return {
    localTags,
    handleTagsChange,
    handleApplyTags,
    handleClearFilters,
    handleRemoveTag,
  }
}
