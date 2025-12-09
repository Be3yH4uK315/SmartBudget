import { createSlice } from '@reduxjs/toolkit'
import { ToastSliceReducers, ToastSliceState } from '@shared/types'
import { getToastInitialState } from './toast.state'

export const toastSlice = createSlice<ToastSliceState, ToastSliceReducers, 'toast', any>({
  name: 'toast',
  initialState: getToastInitialState(),
  reducers: {
    addToast(state, { payload }) {
      state.toasts.push(payload)
    },

    removeToast(state, id) {
      state.toasts = state.toasts.filter((toast) => toast.id !== id.payload)
    },
  },
})

export const toastReducer = toastSlice.reducer
export const { addToast, removeToast } = toastSlice.actions
