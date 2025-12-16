import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { TransactionsScreenSkeleton } from './screens/TransactionsScreen/TransactionsScreenSkeleton'

const TransactionsScreen = lazy(() => import('./screens/TransactionsScreen/TransactionsScreen'))

export const transactionsRoutes = {
  pages: (
    <Route path="transactions">
      <Route
        index
        element={
          <SuspenseFallbackWrapper Fallback={<TransactionsScreenSkeleton />}>
            <TransactionsScreen />
          </SuspenseFallbackWrapper>
        }
      />
    </Route>
  ),
}
