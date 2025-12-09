import { createLazySliceStateSelector } from '@shared/utils/store'
import { getDashboardInitialState } from './dashboard.state'

const sliceStateSelector = createLazySliceStateSelector('dashboard', getDashboardInitialState())

export const selectGoals = sliceStateSelector((state) => state.goals)

export const selectCategories = sliceStateSelector((state) => state.categories)

export const selectBudgetLimit = sliceStateSelector((state) => state.budgetLimit)

export const selectIsDashboardLoading = sliceStateSelector((state) => state.isLoading)
