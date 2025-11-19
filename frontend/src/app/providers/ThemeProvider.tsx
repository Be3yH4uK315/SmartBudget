import { createContext, PropsWithChildren, useCallback, useEffect, useMemo, useState } from 'react'
import '@shared/styles/index.css'
import { CssBaseline, ThemeProvider as MuiThemeProvider } from '@mui/material'
import { darkTheme } from '@shared/styles/darkTheme'
import { lightTheme } from '@shared/styles/lightTheme'

type ColorMode = 'light' | 'dark'

export const ThemeContext = createContext<{
  colorMode: ColorMode
  changeColorMode(newColorMode: ColorMode): void
} | null>(null)

export const ThemeProvider = ({ children }: PropsWithChildren) => {
  const [colorMode, setColorMode] = useState<ColorMode>(() => {
    const stored = window.localStorage.getItem('colorMode')
    if (stored === 'light' || stored === 'dark') {
      return stored
    }

    if (window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }

    return 'light'
  })

  const handleColorModeChange = useCallback((newColorMode: ColorMode) => {
    setColorMode(newColorMode)
  }, [])

  const theme = colorMode === 'light' ? lightTheme : darkTheme

  const contextValue = useMemo(
    () => ({
      colorMode,
      changeColorMode: handleColorModeChange,
    }),
    [colorMode, handleColorModeChange],
  )

  useEffect(() => {
    window.localStorage.setItem('colorMode', colorMode)
  }, [colorMode])

  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)')

    if (media.addEventListener) {
      const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
        setColorMode(e.matches ? 'dark' : 'light')
      }

      media.addEventListener('change', handleChange)
      return () => media.removeEventListener('change', handleChange)
    }
  }, [])

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />

        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  )
}
