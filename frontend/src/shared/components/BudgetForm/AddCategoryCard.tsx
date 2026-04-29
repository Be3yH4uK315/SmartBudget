import { ExpandMoreOutlined } from '@mui/icons-material'
import { Autocomplete, Button, Grid, Stack, TextField } from '@mui/material'
import { CategoryOption, StyledPaper } from '@shared/components'
import { CATEGORIES_ICONS_MAP, TEXT_FIELD_SX } from '@shared/constants'
import { useTheme, useTranslate } from '@shared/hooks'

type Props = {
  categories: number[]
  onSelect: (id: number) => void
  onCancel: () => void
}

export const AddCategoryCard = ({ categories, onSelect, onCancel }: Props) => {
  const theme = useTheme()
  const translateCategory = useTranslate('Categories')
  const translate = useTranslate('BudgetForm.CategoriesLimits.AddCategoryCard')

  const color = theme.colorMode === 'light' ? 'surface.dark' : 'surface.light'

  return (
    <Grid size={{ xs: 12, sm: 6 }}>
      <StyledPaper noElevation paperSx={{ bgcolor: 'surface.main', height: '100%' }}>
        <Stack spacing={2} sx={{ height: '100%', justifyContent: 'center' }}>
          <Autocomplete
            autoFocus
            popupIcon={<ExpandMoreOutlined sx={{ color: 'text.primary' }} />}
            options={categories}
            getOptionLabel={(id) => translateCategory(id)}
            onChange={(_, value) => value && onSelect(value)}
            renderInput={(params) => (
              <TextField {...params} label={translate('placeholder')} sx={TEXT_FIELD_SX(color)} />
            )}
            renderOption={(props, id) => {
              const Icon = CATEGORIES_ICONS_MAP.get(id)!
              return (
                <li {...props} key={id}>
                  <CategoryOption value={id} Icon={Icon} />
                </li>
              )
            }}
          />

          <Button
            onClick={onCancel}
            sx={{
              '&:hover': {
                color: 'error.main',
              },
              height: 'min-content',
            }}
          >
            {translate('cancelButton')}
          </Button>
        </Stack>
      </StyledPaper>
    </Grid>
  )
}
