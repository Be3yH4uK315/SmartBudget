import { GoalsFilters } from '@features/goals/types'
import { useTranslate } from '@shared/hooks'

type GoalsChip = { type: 'tag'; value: string } | { type: 'priority'; value: string }

type Props = {
  localFilters: GoalsFilters
  applyFilters: (value: GoalsFilters) => void
  updateLocalFilters: <K extends keyof GoalsFilters>(key: K, value: GoalsFilters[K]) => void
}

export function useGoalsChips({ localFilters, updateLocalFilters, applyFilters }: Props) {
  const translate = useTranslate('Goals.Tags')

  const chips: GoalsChip[] = []

  localFilters.tags.forEach((tag) => chips.push({ type: 'tag', value: tag }))

  localFilters.priority.forEach((priority) => chips.push({ type: 'priority', value: priority }))

  const getLabel = (chip: GoalsChip) => {
    switch (chip.type) {
      case 'tag':
        return translate(chip.value)

      case 'priority':
        return translate(chip.value)
    }
  }

  const handleDeleteChip = (chip: GoalsChip) => {
    switch (chip.type) {
      case 'tag': {
        const next = {
          ...localFilters,
          tags: localFilters.tags.filter((t) => t !== chip.value),
        }
        updateLocalFilters('tags', next.tags)
        applyFilters(next)
        break
      }

      case 'priority': {
        const next = {
          ...localFilters,
          priority: localFilters.priority.filter((p) => p !== chip.value),
        }
        updateLocalFilters('priority', next.priority)
        applyFilters(next)
        break
      }
    }
  }

  return { chips, getLabel, handleDeleteChip }
}
