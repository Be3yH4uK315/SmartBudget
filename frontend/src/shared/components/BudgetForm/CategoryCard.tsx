import { DeleteOutlined } from '@mui/icons-material'
import { Grid, IconButton, Stack, Typography } from '@mui/material'
import { NumberField, StyledPaper } from '@shared/components'
import { TEXT_FIELD_SX } from '@shared/constants'
import { useTheme, useTranslate } from '@shared/hooks'
import { CategoryRow } from '@shared/types/components'

type Props = {
  category: CategoryRow
  totalLimit: number | null
  onRemove: () => void
  onAmountChange: (value: number) => void
  onPercentChange: (value: number) => void
}

export const CategoryCard = ({
  category,
  totalLimit,
  onRemove,
  onAmountChange,
  onPercentChange,
}: Props) => {
  const theme = useTheme()
  const translateCategory = useTranslate('Categories')
  const translate = useTranslate('BudgetForm.CategoriesLimits.CategoryCard')

  const color = theme.colorMode === 'light' ? 'surface.dark' : 'surface.light'
  const hasTotalLimit = totalLimit != null && totalLimit > 0
  const gridSize = hasTotalLimit ? 6 : 12

  return (
    <Grid size={{ xs: 12, sm: 6 }}>
      <StyledPaper elevation={0} paperSx={{ bgcolor: 'surface.main' }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">{translateCategory(category.categoryId)}</Typography>

          <IconButton sx={{ right: -10 }} onClick={onRemove}>
            <DeleteOutlined sx={{ color: 'secondary.main', ':hover': { color: 'error.main' } }} />
          </IconButton>
        </Stack>

        <Grid container spacing={2}>
          <Grid size={{ xs: gridSize, sm: 12, md: gridSize }}>
            <Stack spacing={1}>
              <Typography variant="caption">{translate('valueHelperText')}</Typography>

              <NumberField
                label={translate('valueLabel')}
                value={category.limit}
                onChange={onAmountChange}
                textFieldSx={TEXT_FIELD_SX(color)}
              />
            </Stack>
          </Grid>

          {hasTotalLimit && (
            <Grid size={{ xs: 6, sm: 12, md: 6 }}>
              <Stack spacing={1}>
                <Typography variant="caption">{translate('percentHelperText')}</Typography>

                <NumberField
                  label={translate('percentLabel')}
                  type="percent"
                  value={category.percent}
                  onChange={onPercentChange}
                  textFieldSx={TEXT_FIELD_SX(color)}
                />
              </Stack>
            </Grid>
          )}
        </Grid>
      </StyledPaper>
    </Grid>
  )
}
