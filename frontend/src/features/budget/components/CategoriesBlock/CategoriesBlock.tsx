import { NoDataFallback } from '@features/budget/components'
import { Category } from '@features/budget/types'
import { Stack, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { CategoryItem } from './CategoryItem'

type Props = {
  isLimited?: boolean
  categories: Category[]
}

export const CategoriesBlock = ({ isLimited = true, categories }: Props) => {
  const translate = useTranslate('CategoryLimitBlock')

  const title = isLimited ? translate('limitedTitle') : translate('unlimitedTitle')
  const subTitle = isLimited ? translate('limitedSubtitle') : translate('unlimitedSubtitle')

  return (
    <StyledPaper paperSx={{ pb: 3 }}>
      <Stack spacing={2}>
        <Stack>
          <Typography variant="h4">{title}</Typography>

          <Typography variant="caption">{subTitle}</Typography>
        </Stack>

        {categories.length === 0 && <NoDataFallback />}

        {categories.length > 0 && (
          <Stack
            gap={1}
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
            }}
          >
            {categories.map((c) => (
              <CategoryItem key={c.categoryId} category={c} isLimited={isLimited} />
            ))}
          </Stack>
        )}
      </Stack>
    </StyledPaper>
  )
}
