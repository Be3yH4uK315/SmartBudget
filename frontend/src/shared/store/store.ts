import { configureStore, UnknownAction } from '@reduxjs/toolkit'
import { rootReducer } from './rootReducer'
import { useDispatch, useSelector } from 'react-redux'

const resettableRootReducer = (
  state: ReturnType<typeof rootReducer> | undefined,
  action: UnknownAction,
) => {
  if (action?.type === 'store/reset') {
    return rootReducer({}, action)
  }

  return rootReducer(state, action)
}

export const store = configureStore({
  reducer: resettableRootReducer,
})

export const getState = store.getState
export const dispatch = store.dispatch

export const useAppDispatch = useDispatch.withTypes<AppDispatch>()

export const useAppSelector = useSelector.withTypes<RootState>()
