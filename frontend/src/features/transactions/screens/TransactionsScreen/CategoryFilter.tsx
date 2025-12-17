import { CategoryOption } from '@features/transactions/components/CategoryOption'
import {
  CATEGORIES_ICONS_MAP,
  CATEGORY_IDS,
} from '@features/transactions/constants/categoriesIcons'
import { Box, MenuItem, Select, SelectChangeEvent } from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props = {
  onChange: (event: SelectChangeEvent<string>) => void
  selectedCategory: number | null
}

export const CategoryFilter = ({ onChange, selectedCategory }: Props) => {
  const translate = useTranslate('Transactions')

  const Icon = selectedCategory ? CATEGORIES_ICONS_MAP.get(selectedCategory) : undefined

  return (
    <Box sx={{ maxWidth: 300, mb: 1 }}>
      <Select
        fullWidth
        displayEmpty
        value={selectedCategory ? String(selectedCategory) : ''}
        onChange={onChange}
        renderValue={(value) => {
          if (!value) return translate('categoryFilter')

          return <CategoryOption value={Number(value)} Icon={Icon} />
        }}
        size="small"
      >
        <MenuItem value="">{translate('emptyCategory')}</MenuItem>
        {CATEGORY_IDS.map((categoryId) => {
          const Icon = CATEGORIES_ICONS_MAP.get(categoryId)
          return (
            <MenuItem key={categoryId} value={String(categoryId)}>
              <CategoryOption value={categoryId} Icon={Icon} />
            </MenuItem>
          )
        })}
      </Select>
    </Box>
  )
}
