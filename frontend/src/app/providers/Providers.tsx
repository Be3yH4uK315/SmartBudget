import { PropsWithChildren } from 'react'
import { LocalizationProvider } from './LocalizationProvider'
import { ReduxProvider } from './ReduxProvider'
import { RouterProvider } from './RouterProvider'
import { ThemeProvider } from './ThemeProvider'
import { ToastProvider } from './Toast/ToastProvider'

export const Providers = ({ children }: PropsWithChildren) => {
  return (
    <LocalizationProvider>
      <ThemeProvider>
        <ToastProvider>
          <ReduxProvider>
            <RouterProvider>{children}</RouterProvider>
          </ReduxProvider>
        </ToastProvider>
      </ThemeProvider>
    </LocalizationProvider>
  )
}
