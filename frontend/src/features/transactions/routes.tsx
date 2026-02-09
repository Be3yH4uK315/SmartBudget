import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { TransactionsChunkScreenSkeleton } from './screens/TransactionsScreen/TransactionsChunkScreenSkeleton'

const TransactionsScreen = lazy(() => import('./screens/TransactionsScreen/TransactionsScreen'))

export const transactionsRoutes = {
  pages: (
    <Route path="transactions">
      <Route
        index
        element={
          <SuspenseFallbackWrapper Fallback={<TransactionsChunkScreenSkeleton />}>
            <TransactionsScreen />
          </SuspenseFallbackWrapper>
        }
      />
    </Route>
  ),
}
