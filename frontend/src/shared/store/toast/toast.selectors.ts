import { toastSlice } from './toast.slice'

export const selectToasts = (state: RootState) => toastSlice.selectSlice(state).toasts
