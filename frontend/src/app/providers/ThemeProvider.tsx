import '@shared/styles/index.css'
import { createContext, PropsWithChildren, useCallback, useMemo, useState } from 'react'
import { CssBaseline, ThemeProvider as MuiThemeProvider } from '@mui/material'
import { darkTheme } from '@shared/styles/darkTheme'
import { lightTheme } from '@shared/styles/lightTheme'

type ColorMode = 'light' | 'dark'

export const ThemeContext = createContext<{
  colorMode: ColorMode
  changeColorMode(newColorMode: ColorMode): void
} | null>(null)

export function ThemeProvider({ children }: PropsWithChildren) {
  const [colorMode, setColorMode] = useState<ColorMode>(() => {
    if (typeof window !== 'undefined') {
      const stored = window.localStorage.getItem('colorMode')
      if (stored === 'light' || stored === 'dark') {
        return stored
      }

      if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
        return 'dark'
      }
    }

    return 'light'
  })

  const handleColorModeChange = useCallback((newColorMode: ColorMode) => {
    setColorMode(newColorMode)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('colorMode', newColorMode)
    }
  }, [])

  const theme = colorMode === 'light' ? lightTheme : darkTheme

  const contextValue = useMemo(
    () => ({
      colorMode,
      changeColorMode: handleColorModeChange,
    }),
    [colorMode, handleColorModeChange],
  )

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />

        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  )
}
