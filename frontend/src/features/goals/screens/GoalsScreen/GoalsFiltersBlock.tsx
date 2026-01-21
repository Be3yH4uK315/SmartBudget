import { AVAILABLE_TAGS, PRIORITIES } from '@features/goals/constants/tags'
import { useGoalsFilters } from '@features/goals/hooks'
import { GoalsFilters } from '@features/goals/types'
import {
  Button,
  Checkbox,
  Chip,
  FormControl,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material'
import { StyledBox } from '@shared/components'
import { useTranslate } from '@shared/hooks'

type Props = {
  filters: GoalsFilters
}

export const GoalsFiltersBlock = ({ filters }: Props) => {
  const translate = useTranslate('Goals.Tags')

  const { localTags, handleTagsChange, handleApplyTags, handleClearFilters, handleRemoveTag } =
    useGoalsFilters(filters)

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', sm: 'row' }} sx={{ justifyContent: 'space-between' }}>
        <FormControl sx={{ minWidth: 200, maxWidth: 250 }}>
          <Select
            multiple
            displayEmpty
            value={localTags}
            onChange={handleTagsChange}
            onClose={handleApplyTags}
            renderValue={(value) =>
              value.length === 0
                ? translate('placeholder')
                : translate('selected', { value: value.length })
            }
            size="small"
            sx={{
              height: 'auto',
              bgcolor: 'surface.light',
              '& .MuiOutlinedInput-notchedOutline': {
                borderWidth: 1,
              },
              '& .MuiSelect-select': {
                py: 1,
              },
            }}
          >
            {[...AVAILABLE_TAGS, ...PRIORITIES].map((tag) => (
              <MenuItem key={tag} value={tag}>
                <Checkbox
                  checked={localTags.includes(tag)}
                  sx={{
                    color: 'primary.main',
                  }}
                />

                <Typography>{translate(tag)}</Typography>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {filters.tags?.length > 0 && (
          <Button onClick={handleClearFilters} sx={{ height: 'min-content' }} variant="yellow">
            {translate('clear')}
          </Button>
        )}
      </Stack>

      {localTags.length > 0 && (
        <StyledBox>
          {localTags.map((tag) => (
            <Chip
              key={tag}
              label={translate(tag)}
              onDelete={() => handleRemoveTag(tag)}
              sx={{
                bgcolor: 'primary.main',
                color: '#333',
                typography: 'caption',
                '& .MuiSvgIcon-root': {
                  color: '#333',
                },
              }}
            />
          ))}
        </StyledBox>
      )}
    </Stack>
  )
}
