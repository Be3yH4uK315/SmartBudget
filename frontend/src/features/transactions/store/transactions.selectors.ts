import { createLazySliceStateSelector } from '@shared/utils/store'
import { getTransactionsInitialState } from './transactions.state'

const sliceStateSelector = createLazySliceStateSelector(
  'transactions',
  getTransactionsInitialState(),
)

export const selectTransactions = sliceStateSelector((state) => state.transactions)
export const selectIsTransactionsLoading = sliceStateSelector((state) => state.isLoading)
export const selectTransactionsIsLast = sliceStateSelector((state) => state.isLast)
export const selectTransactionsOffset = sliceStateSelector((state) => state.offset)

export const selectIsCategoryChanging = sliceStateSelector((state) => state.isCategoryChanging)

export const selectAvailableGoals = sliceStateSelector((state) => state.availableGoals)
export const selectIsImportLoading = sliceStateSelector((state) => state.isImportLoading)
