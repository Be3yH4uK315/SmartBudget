import { configureStore, UnknownAction } from '@reduxjs/toolkit'
import { useDispatch, useSelector } from 'react-redux'
import { createErrorMiddleware } from './middleware'
import { rootReducer } from './rootReducer'

const resettableRootReducer = (
  state: ReturnType<typeof rootReducer> | undefined,
  action: UnknownAction,
) => {
  if (action?.type === 'store/reset') {
    return rootReducer({}, action)
  }

  return rootReducer(state, action)
}

export const createAppStore = (translate: (key: string) => string) => {
  const errorMiddleware = createErrorMiddleware(translate)

  return configureStore({
    reducer: resettableRootReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({ serializableCheck: false }).concat(errorMiddleware),
  })
}

export const store = createAppStore((key) => key)

export const getState = store.getState
export const dispatch = store.dispatch

export const useAppDispatch = useDispatch.withTypes<AppDispatch>()

export const useAppSelector = useSelector.withTypes<RootState>()
