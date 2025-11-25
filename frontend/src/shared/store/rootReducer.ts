import { combineSlices } from '@reduxjs/toolkit'
import { userSlice } from './user'

export interface AppLazySlices extends Record<string, object> {}

export const rootReducer = combineSlices(userSlice).withLazyLoadedSlices<AppLazySlices>()
