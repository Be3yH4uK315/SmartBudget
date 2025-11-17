/** Тип корневого состояния приложения */
type RootState = ReturnType<typeof import('@shared/store/store').store.getState>

/** Dispatch для ассинхронных действий */
type AppDispatch = typeof import('@shared/store/store').store.dispatch

type LoadingStatus = 'idle' | 'loading' | 'fulfilled' | 'error'
