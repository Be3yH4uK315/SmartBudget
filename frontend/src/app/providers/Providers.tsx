import { PropsWithChildren } from 'react'
import { LocalizationProvider } from './LocalizationProvider'
import { ReduxProvider } from './ReduxProvider'
import { RouterProvider } from './RouterProvider'
import { ThemeProvider } from './ThemeProvider'

export function Providers({ children }: PropsWithChildren) {
  return (
    <ReduxProvider>
      <RouterProvider>
        <ThemeProvider>
          <LocalizationProvider>{children}</LocalizationProvider>
        </ThemeProvider>
      </RouterProvider>
    </ReduxProvider>
  )
}
