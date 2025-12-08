type ToastOptions = {
  messageKey: string
  titleKey?: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

type ToastSliceState = {
  toasts: ToastOptions[]
}

type ToastSliceReducers = SliceCaseReducers<ToastSliceState> & {
  addToast(state: ToastSliceState, action: PayloadAction<ToastOptions>): void

  removeToast(state: ToastSliceState): void
}
