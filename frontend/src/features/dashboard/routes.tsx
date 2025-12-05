import { lazy, Suspense } from 'react'
import { Container } from '@mui/material'
import { Route } from 'react-router'
import { DashboardScreenSkeleton } from './screens/DashboardScreenSkeleton'

const DashboardScreen = lazy(() => import('./screens/DashboardScreen'))

export const dashboardRoutes = {
  pages: (
    <Route
      path="main"
      index
      element={
        <Suspense
          fallback={
            <Container maxWidth="lg" sx={{ pt: 4 }}>
              <DashboardScreenSkeleton />
            </Container>
          }
        >
          <DashboardScreen />
        </Suspense>
      }
    />
  ),
}
