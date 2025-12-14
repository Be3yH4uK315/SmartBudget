import { lazy, Suspense } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { TransactionsScreenSkeleton } from './screens/TransactionsScreenSkeleton'

const TransactionsScreen = lazy(() => import('./screens/TransactionsScreen'))
const TransactionModal = lazy(() => import('./screens/TransactionModal/TransactionModal'))

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

  modals: (
    <Route path="transactions">
      <Route
        path=":id"
        element={
          <Suspense>
            <TransactionModal />
          </Suspense>
        }
      />
    </Route>
  ),
}
