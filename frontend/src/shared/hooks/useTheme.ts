import { useContext } from 'react'
import { ThemeContext } from '@app/providers/ThemeProvider'

export const useTheme = () => {
  const context = useContext(ThemeContext)

  if (!context)
    throw new Error(
      'ThemeContext context not found (useTheme must be used inside <ThemeProvider />)',
    )

  return context
}
