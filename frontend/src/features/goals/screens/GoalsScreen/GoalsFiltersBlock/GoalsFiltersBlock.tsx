import { AVAILABLE_TAGS, PRIORITIES } from '@features/goals/constants/tags'
import { useGoalsFilters } from '@features/goals/hooks'
import { GoalsFilters, Priority, Tag } from '@features/goals/types'
import { Button, Chip, Stack } from '@mui/material'
import { StyledBox } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { FiltersSelect } from './FiltersSelect'

type Props = {
  filters: GoalsFilters
}

export const GoalsFiltersBlock = ({ filters }: Props) => {
  const translate = useTranslate('Goals.Tags')

  const {
    handleClearFilters,
    localPriority,
    handlePriorityChange,
    handleApplyPriority,
    handleRemovePriority,
    localTags,
    handleTagsChange,
    handleApplyTags,
    handleRemoveTag,
  } = useGoalsFilters(filters)

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between' }}>
        <Stack spacing={2} direction={'row'}>
          <FiltersSelect<Tag>
            value={localTags}
            items={AVAILABLE_TAGS}
            placeholder={translate('placeholder.tags')}
            onChange={handleTagsChange}
            onClose={handleApplyTags}
          />

          <FiltersSelect<Priority>
            value={localPriority}
            items={PRIORITIES}
            placeholder={translate('placeholder.priority')}
            onChange={handlePriorityChange}
            onClose={handleApplyPriority}
          />
        </Stack>

        {filters.tags?.length > 0 ||
          (filters.priority?.length > 0 && (
            <Button onClick={handleClearFilters} sx={{ height: 'min-content' }} variant="yellow">
              {translate('clear')}
            </Button>
          ))}
      </Stack>

      {(localTags.length > 0 || localPriority.length > 0) && (
        <StyledBox>
          {[...localTags, ...localPriority].map((item) => (
            <Chip
              key={item}
              label={translate(item)}
              onDelete={() =>
                localTags.includes(item as any)
                  ? handleRemoveTag(item as any)
                  : handleRemovePriority(item as any)
              }
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
