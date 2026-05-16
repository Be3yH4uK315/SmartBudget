import { PropsWithChildren } from 'react'
import { LocalizationProvider as MUILocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { LocalizationProvider } from './LocalizationProvider'
import { NotificationsProvider } from './NotificationProvider'
import { ReduxProvider } from './ReduxProvider'
import { RouterProvider } from './RouterProvider'
import { ThemeProvider } from './ThemeProvider'
import { ToastProvider } from './Toast/ToastProvider'

export const Providers = ({ children }: PropsWithChildren) => {
  return (
    <ReduxProvider>
      <RouterProvider>
        <ThemeProvider>
          <LocalizationProvider>
            <MUILocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="ru-RU">
              <ToastProvider>
                <NotificationsProvider>{children}</NotificationsProvider>
              </ToastProvider>
            </MUILocalizationProvider>
          </LocalizationProvider>
        </ThemeProvider>
      </RouterProvider>
    </ReduxProvider>
  )
}
