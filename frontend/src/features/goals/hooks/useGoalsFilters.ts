import { useState } from 'react'
import { getGoals, resetFilters, setPriority, setTags } from '@features/goals/store/goals'
import { GoalsFilters, Priority, Tag } from '@features/goals/types'
import { SelectChangeEvent } from '@mui/material'
import { useAppDispatch } from '@shared/store'

export function useGoalsFilters(filters: GoalsFilters) {
  const dispatch = useAppDispatch()

  const [localTags, setLocalTags] = useState<Tag[]>(filters.tags)
  const [localPriority, setLocalPriority] = useState<Priority[]>(filters.priority)

  const handleTagsChange = (e: SelectChangeEvent<Tag[]>) => {
    const value = e.target.value
    setLocalTags(typeof value === 'string' ? (value.split(',') as Tag[]) : value)
  }

  const handlePriorityChange = (e: SelectChangeEvent<Priority[]>) => {
    const value = e.target.value
    setLocalPriority(typeof value === 'string' ? (value.split(',') as Priority[]) : value)
  }

  const handleApplyTags = () => {
    if (localTags === filters.tags) return

    dispatch(setTags(localTags))
    dispatch(getGoals())
  }

  const handleApplyPriority = () => {
    if (localPriority === filters.priority) return

    dispatch(setPriority(localPriority))
    dispatch(getGoals())
  }

  const handleRemovePriority = (priority: Priority) => {
    const next = localPriority.filter((p) => p !== priority)
    setLocalPriority(next)

    dispatch(setPriority(next))
    dispatch(getGoals())
  }

  const handleRemoveTag = (tag: Tag) => {
    const next = localTags.filter((t) => t !== tag)
    setLocalTags(next)

    dispatch(setTags(next))
    dispatch(getGoals())
  }

  const handleClearFilters = () => {
    if (filters.tags?.length === 0 && filters.priority?.length === 0) return

    setLocalTags([])

    dispatch(resetFilters())
    dispatch(getGoals())
  }

  return {
    localPriority,
    handlePriorityChange,
    handleApplyPriority,
    handleRemovePriority,
    localTags,
    handleTagsChange,
    handleApplyTags,
    handleClearFilters,
    handleRemoveTag,
  }
}
