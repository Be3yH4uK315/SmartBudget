/* eslint-disable react-hooks/static-components */
import { ShoppingBagOutlined } from '@mui/icons-material'
import { Box, SxProps } from '@mui/material'
import { CATEGORIES_ICONS_MAP } from '@shared/constants/categoriesIcons'

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
  )
}
