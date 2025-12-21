import { lazy, Suspense } from 'react'
import { Container } from '@mui/material'
import { Route } from 'react-router'

const BudgetScreen = lazy(() => import('./screens/BudgetScreen'))

export const budgetRoutes = {
  pages: (
    <Route
      path="budget"
      index
      element={
        <Suspense>
          <BudgetScreen />
        </Suspense>
      }
    />
  ),
}
