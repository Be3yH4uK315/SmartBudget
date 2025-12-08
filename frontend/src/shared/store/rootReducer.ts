import { combineSlices } from '@reduxjs/toolkit'
import { toastSlice } from './toast'
import { userSlice } from './user'

export interface AppLazySlices extends Record<string, object> {}

export const rootReducer = combineSlices(
  userSlice,
  toastSlice,
).withLazyLoadedSlices<AppLazySlices>()
