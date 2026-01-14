import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'

const SecurityScreen = lazy(() => import('./screens/SecurityScreen/SecurityScreen'))

export const settingsRoutes = {
  pages: (
    <Route path="settings">
      <Route index element={<SecurityScreen />} />
    </Route>
  ),
}
