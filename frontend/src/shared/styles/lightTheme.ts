import { createTheme } from '@mui/material'
import { ruRU } from '@mui/x-date-pickers/locales'
import { breakpoints } from './breakpoints'
import { components } from './components'
import { paletteLight } from './paletteLight'
import { shadows } from './shadows'
import { typography } from './typography'

export const lightTheme = createTheme(
  {
    typography,
    palette: paletteLight,
    components,
    shadows,
    breakpoints,
    shape: {
      borderRadius: 6,
    },
  },
  ruRU,
)
