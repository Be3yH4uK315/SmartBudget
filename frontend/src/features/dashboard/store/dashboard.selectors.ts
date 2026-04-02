import { createLazySliceStateSelector } from '@shared/utils/store'
import { getDashboardInitialState } from './dashboard.state'

const sliceStateSelector = createLazySliceStateSelector('dashboard', getDashboardInitialState())

export const selectGoals = sliceStateSelector((state) => state.goals)

export const selectCategories = sliceStateSelector((state) => state.categories)

export const selectBudgetLimit = sliceStateSelector((state) => state.budgetLimit)

export const selectIsDashboardBudgetLoading = sliceStateSelector((state) => state.isBudgetLoading)

export const selectIsDashboardGoalsLoading = sliceStateSelector((state) => state.isGoalsLoading)
