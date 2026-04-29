import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { BudgetChunkScreenSkeleton } from './screens/BudgetScreen/BudgetChunkScreenSkeleton'
import { NotificationsScreenSkeleton } from './screens/NotificationsScreen/NotificationsScreenSkeleton'
import { SecurityScreenSkeleton } from './screens/SecurityScreen/SecurityScreenSkeleton'

const SecurityScreen = lazy(() => import('./screens/SecurityScreen/SecurityScreen'))
const SettingsScreen = lazy(() => import('./screens/SettingsScreen'))
const BudgetScreen = lazy(() => import('./screens/BudgetScreen/BudgetScreen'))
const NotificationsScreen = lazy(() => import('./screens/NotificationsScreen/NotificationsScreen'))

export const settingsRoutes = {
  pages: (
    <Route path="settings">
      <Route
        index
        element={
          <SuspenseFallbackWrapper>
            <SettingsScreen />
          </SuspenseFallbackWrapper>
        }
      />

      <Route
        path="security"
        element={
          <SuspenseFallbackWrapper Fallback={<SecurityScreenSkeleton />}>
            <SecurityScreen />
          </SuspenseFallbackWrapper>
        }
      />

      <Route
        path="budget"
        element={
          <SuspenseFallbackWrapper Fallback={<BudgetChunkScreenSkeleton />}>
            <BudgetScreen />
          </SuspenseFallbackWrapper>
        }
      />

      <Route
        path="notifications"
        element={
          <SuspenseFallbackWrapper Fallback={<NotificationsScreenSkeleton />}>
            <NotificationsScreen />
          </SuspenseFallbackWrapper>
        }
      />
    </Route>
  ),
}
