import { lazy, Suspense } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { LoadingScreen } from '@shared/screens/LoadingScreen'
import { Route } from 'react-router'
import { TransactionsScreenSkeleton } from './screens/TransactionsScreen/TransactionsScreenSkeleton'

const TransactionsScreen = lazy(() => import('./screens/TransactionsScreen/TransactionsScreen'))
const TransactionModalLayout = lazy(
  () => import('./screens/TransactionModal/TransactionModalLayout'),
)
const TransactionInfo = lazy(() => import('./screens/TransactionModal/TransactionInfo'))
const ChangeCategory = lazy(() => import('./screens/TransactionModal/ChangeCategory'))

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
    <Route
      path="transactions"
      element={
        <Suspense>
          <TransactionModalLayout />
        </Suspense>
      }
    >
      <Route
        path=":id"
        element={
          <SuspenseFallbackWrapper Fallback={<LoadingScreen />}>
            <TransactionInfo />
          </SuspenseFallbackWrapper>
        }
      />

      <Route
        path=":id/category"
        element={
          <SuspenseFallbackWrapper Fallback={<LoadingScreen />}>
            <ChangeCategory />
          </SuspenseFallbackWrapper>
        }
      />
    </Route>
  ),
}
