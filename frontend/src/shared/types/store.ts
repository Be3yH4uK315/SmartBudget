/** Тип корневого состояния приложения */
export type RootState = ReturnType<typeof import('@shared/store/store').store.getState>

/** Dispatch для ассинхронных действий */
export type AppDispatch = typeof import('@shared/store/store').store.dispatch

export type LoadingStatus = 'idle' | 'loading' | 'fulfilled' | 'error'
