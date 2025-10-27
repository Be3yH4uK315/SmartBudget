import { PropsWithChildren } from 'react'
import { ReduxProvider } from './ReduxProvider'
import { ThemeProvider } from './ThemeProvider'
import { RouterProvider } from './RouterProvider'

export function Providers({ children }: PropsWithChildren) {
  return (
    <ReduxProvider>
      <RouterProvider>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </RouterProvider>
    </ReduxProvider>
  )
}
