import { combineSlices } from '@reduxjs/toolkit'
import { modalSlice } from './modal'
import { toastSlice } from './toast'
import { userSlice } from './user'

export interface AppLazySlices extends Record<string, object> {}

export const rootReducer = combineSlices(
  userSlice,
  toastSlice,
  modalSlice,
).withLazyLoadedSlices<AppLazySlices>()
