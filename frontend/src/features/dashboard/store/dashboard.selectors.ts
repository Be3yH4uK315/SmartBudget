import { createLazySliceStateSelector } from '@shared/utils/store'
import { getDashboardInitialState } from './dashboard.state'

const sliceStateSelector = createLazySliceStateSelector('dashboard', getDashboardInitialState())

export const selectDashboardData = sliceStateSelector((state) => state)
