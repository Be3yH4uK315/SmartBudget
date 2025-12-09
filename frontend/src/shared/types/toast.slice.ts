import { PayloadAction, SliceCaseReducers } from "./reduxToolkit"

export type ToastOptions = {
  id: number
  messageKey: string
  titleKey?: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
}

export type ToastSliceState = {
  toasts: ToastOptions[]
}

export type ToastSliceReducers = SliceCaseReducers<ToastSliceState> & {
  addToast(state: ToastSliceState, action: PayloadAction<ToastOptions>): void

  removeToast(state: ToastSliceState, action: PayloadAction<number>): void
}