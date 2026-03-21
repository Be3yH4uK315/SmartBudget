import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { NotificationsChunkScreenSkeleton } from './screens/NotificationsChunkScreenSkeleton'

const NotificationsScreen = lazy(() => import('./screens/NotificationsScreen'))

export const notificationsRoutes = {
  pages: (
    <Route path="notifications">
      <Route
        index
        element={
          <SuspenseFallbackWrapper Fallback={<NotificationsChunkScreenSkeleton />}>
            <NotificationsScreen />
          </SuspenseFallbackWrapper>
        }
      />
    </Route>
  ),
}
