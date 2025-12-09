import type { EntityState as RTKEntityState, EntityId } from '@reduxjs/toolkit'
import { AppDispatch, RootState } from './store'

export type PayloadAction<
  P = void,
  T extends string = string,
  M = never,
  E = never,
> = import('@reduxjs/toolkit').PayloadAction<P, T, M, E>

export type SliceCaseReducers<T> = import('@reduxjs/toolkit').SliceCaseReducers<T>

export type EntityState<T, Id extends EntityId = number> = RTKEntityState<T, Id>

export type AppStartListening = import('@reduxjs/toolkit').TypedStartListening<
  RootState,
  AppDispatch
>
