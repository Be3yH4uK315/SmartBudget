import { createSlice } from '@reduxjs/toolkit'
import { getToastInitialState } from './toast.state'

export const toastSlice = createSlice<ToastSliceState, ToastSliceReducers, 'toast', any>({
  name: 'toast',
  initialState: getToastInitialState(),
  reducers: {
    addToast(state, { payload }) {
      state.toasts.push(payload)
    },

    removeToast(state) {
      state.toasts.shift()
    },
  },
})

export const toastReducer = toastSlice.reducer
export const { addToast, removeToast } = toastSlice.actions
