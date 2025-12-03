import { lazy, Suspense } from 'react'
import { Route } from 'react-router'

const DashboardScreen = lazy(() => import('./screens/DashboardScreen'))

export const dashboardRoutes = {
  pages: (
    <Route
      path="main"
      index
      element={
        <Suspense>
          <DashboardScreen />
        </Suspense>
      }
    />
  ),
}
