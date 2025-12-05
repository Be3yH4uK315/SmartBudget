import { lazy, Suspense } from 'react'
import { Route } from 'react-router'
import { DashboardScreenSkeleton } from './screens/DashboardScreenSkeleton'

const DashboardScreen = lazy(() => import('./screens/DashboardScreen'))

export const dashboardRoutes = {
  pages: (
    <Route
      path="main"
      index
      element={
        <Suspense fallback={<DashboardScreenSkeleton />}>
          <DashboardScreen />
        </Suspense>
      }
    />
  ),
}
