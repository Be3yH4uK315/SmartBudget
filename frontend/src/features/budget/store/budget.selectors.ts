import { createLazySliceStateSelector } from '@shared/utils/store'
import { getBudgetInitialState } from './budget.state'

const sliceStateSelector = createLazySliceStateSelector('budget', getBudgetInitialState())

export const selectBudgetCategories = sliceStateSelector((state) => state.categories)

export const selectIsAutoRenew = sliceStateSelector((state) => state.isAutoRenew)

export const selectBudgetCurrentValue = sliceStateSelector((state) => state.currentValue)

export const selectBudgetTotalLimit = sliceStateSelector((state) => state.totalLimit)

export const selectIsBudgetLoading = sliceStateSelector((state) => state.isLoading)
