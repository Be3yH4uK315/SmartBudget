import { AVAILABLE_TAGS, PRIORITIES } from '@features/goals/constants/tags'
import { useGoalsChips } from '@features/goals/hooks/useGoalsChips'
import { GoalsFilters, Priority, Tag } from '@features/goals/types'
import { Button, Chip, Stack } from '@mui/material'
import { FiltersSelect, StyledBox } from '@shared/components'
import { useTranslate } from '@shared/hooks'

type Props = {
  isDirty: boolean
  localFilters: GoalsFilters
  handleClearFilters: () => void
  handleApply: () => void
  applyFilters: (value: any) => void
  updateLocalFilters: <K extends keyof GoalsFilters>(key: K, value: GoalsFilters[K]) => void
}

export const GoalsFiltersBlock = ({ ...props }: Props) => {
  const translate = useTranslate('Goals.Tags')

  const { handleClearFilters, handleApply, isDirty, localFilters, updateLocalFilters } = props

  const { chips, getLabel, handleDeleteChip } = useGoalsChips(props)

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between' }}>
        <Stack spacing={2} direction={'row'}>
          <FiltersSelect<Tag>
            multiple
            value={localFilters.tags}
            items={AVAILABLE_TAGS}
            translateItemKey={'Goals.Tags'}
            translateKey={'Goals.Filters'}
            placeholderKey={'placeholder.tags'}
            onChange={(e) => updateLocalFilters('tags', e.target.value)}
            onClose={handleApply}
          />

          <FiltersSelect<Priority>
            multiple
            value={localFilters.priority}
            items={PRIORITIES}
            translateItemKey={'Goals.Tags'}
            translateKey={'Goals.Filters'}
            placeholderKey={'placeholder.priority'}
            onChange={(e) => updateLocalFilters('priority', e.target.value)}
            onClose={handleApply}
          />
        </Stack>

        {(localFilters.tags?.length > 0 || localFilters.priority?.length > 0) && (
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
