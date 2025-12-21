import { Category } from '@features/budget/types'
import { Stack, Typography } from '@mui/material'
import { PercentLine, StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { formatCurrency } from '@shared/utils/formatCurrency'

type Props = {
  category: Category
  isLimited?: boolean
}

export const CategoryItem = ({ isLimited = true, category }: Props) => {
  const translate = useTranslate('Categories')

  return (
    <StyledPaper
      elevation={0}
      paperSx={{
        bgcolor: 'surface.main',
      }}
    >
      <Stack
        direction={isLimited ? 'column' : 'row'}
        justifyContent={'space-between'}
        alignItems={isLimited ? 'normal' : 'center'}
      >
        <Typography variant="h5" fontSize={'1.25rem'}>
          {translate(category.categoryId)}
        </Typography>

        {isLimited && <PercentLine currentValue={category.currentValue} limit={category.limit} />}

        {!isLimited && <Typography>{formatCurrency(category.currentValue)}</Typography>}
      </Stack>
    </StyledPaper>
  )
}
