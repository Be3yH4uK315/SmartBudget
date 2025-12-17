import { ToastOptions } from '@shared/types'

export const DEFAULT_DURATION: Record<ToastOptions['type'], number> = {
  success: 3000,
  info: 5000,
  warning: 5000,
  error: 7000,
}
