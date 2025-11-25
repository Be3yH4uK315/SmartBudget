import { Breakpoint, useMediaQuery, useTheme } from '@mui/material'

export const useScreenSizeValue = (breakpoint: Breakpoint, value: any, defaultValue: any) => {
  const theme = useTheme()

  return useMediaQuery(theme.breakpoints.down(breakpoint)) ? value : defaultValue
}