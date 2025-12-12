import { lazy, Suspense } from 'react'
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { Container } from '@mui/material'
import { Route } from 'react-router'

const TransactionsScreen = lazy(() => import('./screens/TransactionsScreen'))

export const transactionRoutes = {
  pages: (
    <Route
      path="transactions"
      index
      element={
        <Suspense>
          <TransactionsScreen />
        </Suspense>
      }
    />
  ),
}
