import { ToastSliceState } from '@shared/types'

export function getToastInitialState(): ToastSliceState {
  return {
    toasts: [],
  }
}
