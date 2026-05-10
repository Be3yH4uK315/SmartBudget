import { DarkModeOutlined, LightModeOutlined } from '@mui/icons-material'
import { IconButton } from '@mui/material'
import { useTheme } from '@shared/hooks'

export const ThemeButton = () => {
  const { colorMode, changeColorMode } = useTheme()

  const handleClick = () => changeColorMode(colorMode === 'light' ? 'dark' : 'light')

  return (
    <IconButton
      size="large"
      onClick={handleClick}
      sx={{
        borderRadius: 1,
        backgroundColor: 'surface.light',
      }}
    >
      {colorMode === 'light' ? (
        <DarkModeOutlined sx={{ color: 'gray.main' }} />
      ) : (
        <LightModeOutlined sx={{ color: 'gray.main' }} />
      )}
    </IconButton>
  )
}
