import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { BudgetScreenSkeleton } from './screens/BudgetScreen'

const BudgetScreen = lazy(() => import('./screens/BudgetScreen'))

export const budgetRoutes = {
  pages: (
    <Route
      path="budget"
      index
      element={
        <SuspenseFallbackWrapper Fallback={<BudgetScreenSkeleton />}>
          <BudgetScreen />
        </SuspenseFallbackWrapper>
      }
    />
  ),
}
