import { OVERFLOW_STYLES } from '@features/budget/constants/overflowStyles'
import { Category } from '@features/budget/types'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import { Box, Stack, Typography, useTheme } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { formatPercent } from '@shared/utils'

type Props = {
  variant: 'overflow' | 'preOverflow'
  categories: Category[]
}

export const OverflowCategoriesBlock = ({ variant, categories }: Props) => {
  const translate = useTranslate('Overflow')
  const translateCategory = useTranslate('Categories')
  const theme = useTheme()

  const { borderColor, fontColor, bgColor } = OVERFLOW_STYLES[variant](theme)

  return (
    <StyledPaper paperSx={{ border: `2px solid ${borderColor}`, bgcolor: bgColor, px: 2 }}>
      <Stack>
        <Typography
          variant="h5"
          component="div"
          sx={{ display: 'flex', alignItems: 'center', gap: 1, color: fontColor }}
        >
          {translate(`${variant}Title`)}

          <InfoOutlinedIcon fontSize="small" />
        </Typography>

        <Typography variant="caption" color={fontColor}>
          {translate(`${variant}Subtitle`, { count: categories.length })}
        </Typography>

        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0 8px',
          }}
        >
          {categories.map((c) => (
            <Typography key={c.categoryId} variant="caption" color={fontColor}>
              {translateCategory(c.categoryId) + ` (${formatPercent(c.currentValue / c.limit)})`}
            </Typography>
          ))}
        </Box>
      </Stack>
    </StyledPaper>
  )
}
