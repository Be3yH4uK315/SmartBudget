import { createTheme } from '@mui/material'
import { breakpoints } from './breakpoints'
import { components } from './components'
import { paletteDark } from './paletteDark'
import { shadows } from './shadows'
import { typography } from './typography'

export const darkTheme = createTheme({
  typography,
  palette: paletteDark,
  components,
  shadows,
  breakpoints,
  shape: {
    borderRadius: 6,
  },
})
