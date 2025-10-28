import { PropsWithChildren } from 'react'
import { ReduxProvider } from './ReduxProvider'
import { ThemeProvider } from './ThemeProvider'
import { RouterProvider } from './RouterProvider'
import { LocalizationProvider } from './LocalizationProvider'

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
