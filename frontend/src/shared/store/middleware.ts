import { showToast } from '@app/providers/Toast/globalToast'
import { isRejectedWithValue, Middleware } from '@reduxjs/toolkit'

export const createErrorMiddleware =
  (translate: (value: string) => string): Middleware =>
  () =>
  (next) =>
  (action: unknown) => {
    const result = next(action)

    if (isRejectedWithValue(action)) {
      // console.log(action)
      const typedAction = action as { payload?: string }
      const message = typedAction.payload || 'UnknownError'

      showToast({
        type: 'error',
        title: translate('title'),
        message: translate(`message.${message}`),
      })
    }

    return result
  }
