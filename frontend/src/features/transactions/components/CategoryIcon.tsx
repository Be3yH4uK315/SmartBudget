/* eslint-disable react-hooks/static-components */
import { Suspense } from 'react'
import { CATEGORIES_ICONS_MAP } from '@features/transactions/constants/categoriesIcons'
import { ShoppingBagOutlined } from '@mui/icons-material'
import { Box, SxProps } from '@mui/material'
import { useTheme } from '@shared/hooks'

type Props = {
  categoryId: number
  size?: number
  boxSx?: SxProps
  iconSx?: SxProps
}

export const CategoryIcon = ({ categoryId, size = 70, boxSx, iconSx }: Props) => {
  const IconComponent = CATEGORIES_ICONS_MAP.get(categoryId)

  if (!IconComponent) {
    return <ShoppingBagOutlined sx={{ width: size, height: size }} />
  }

  return (
    <Suspense fallback={<Box width={size} height={size} />}>
      <Box
        sx={{
          width: size,
          height: size,
          bgcolor: 'surface.light',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          p: 8,
          borderRadius: `${size}px`,
          ...boxSx,
        }}
      >
        <IconComponent sx={{ width: size / 1.5, height: size / 1.5, ...iconSx }} />
      </Box>
    </Suspense>
  )
}
