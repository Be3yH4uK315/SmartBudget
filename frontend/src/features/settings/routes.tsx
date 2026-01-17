import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { SecurityScreenSkeleton } from './screens/SecurityScreen/SecurityScreenSkeleton'

const SecurityScreen = lazy(() => import('./screens/SecurityScreen/SecurityScreen'))
const SettingsScreen = lazy(() => import('./screens/SettingsScreen'))

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
    </Route>
  ),
}
