import { createLazySliceStateSelector } from '@shared/utils/store'
import { getBudgetInitialState } from './budget.state'

const sliceStateSelector = createLazySliceStateSelector('budget', getBudgetInitialState())

export const selectBudgetCategories = sliceStateSelector((state) => state.categories)

export const selectIsAutoRenew = sliceStateSelector((state) => state.isAutoRenew)

export const selectBudgetTotalLimit = sliceStateSelector((state) => state.totalLimitAmount)

export const selectBudgetTotalIncome = sliceStateSelector((state) => state.totalIncomeAmount)

export const selectIsBudgetLoading = sliceStateSelector((state) => state.isLoading)
