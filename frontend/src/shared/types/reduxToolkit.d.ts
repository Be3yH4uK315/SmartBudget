type PayloadAction<
  P = void,
  T extends string = string,
  M = never,
  E = never,
> = import('@reduxjs/toolkit').PayloadAction<P, T, M, E>

type SliceCaseReducers<T> = import('@reduxjs/toolkit').SliceCaseReducers<T>

type EntityState<T, Id = number> = import('@reduxjs/toolkit').EntityState<T, Id>

type AppStartListening = import('@reduxjs/toolkit').TypedStartListening<RootState, AppDispatch>
