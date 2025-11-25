import { createTheme } from '@mui/material'
import { breakpoints } from './breakpoints'
import { components } from './components'
import { paletteLight } from './paletteLight'
import { shadows } from './shadows'
import { typography } from './typography'

export const lightTheme = createTheme({
  typography,
  palette: paletteLight,
  components,
  shadows,
  breakpoints,
  shape: {
    borderRadius: 6,
  },
})
