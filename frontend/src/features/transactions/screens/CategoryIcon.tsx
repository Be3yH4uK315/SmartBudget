/* eslint-disable react-hooks/static-components */
import { Suspense } from 'react'
import { CATEGORIES_ICONS_MAP } from '@features/transactions/constants/categoriesIcons'
import { ShoppingBagOutlined } from '@mui/icons-material'
import { Box } from '@mui/material'

type Props = {
  categoryId: number
  size?: number
}

export const CategoryIcon = ({ categoryId, size = 70 }: Props) => {
  const IconComponent = CATEGORIES_ICONS_MAP.get(categoryId)

  if (!IconComponent) {
    return <ShoppingBagOutlined sx={{ width: size, height: size }} />
  }

  return (
    <Suspense fallback={<Box width={size} height={size} />}>
      <Box
        width={size}
        height={size}
        bgcolor="surface.light"
        display="flex"
        justifyContent="center"
        alignItems="center"
        p={8}
        borderRadius={`${size}px`}
      >
        <IconComponent sx={{ width: size, height: size }} />
      </Box>
    </Suspense>
  )
}
