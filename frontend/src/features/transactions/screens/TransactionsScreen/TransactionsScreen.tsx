import { useEffect } from 'react'
import { transactionsApi, transactionsMock } from '@features/transactions/api'
import { useTransactionsFilters } from '@features/transactions/hooks'
import {
  clearTransactionsState,
  selectIsTransactionsLoading,
  selectTransactions,
  selectTransactionsIsLast,
} from '@features/transactions/store'
import { Transaction } from '@features/transactions/types'
import { Stack } from '@mui/material'
import { EmptyList, ScreenContent, SearchBar, withAuth } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { TransactionsFiltersBlock } from './TransactionsFilters'
import { TransactionLine, TransactionsList } from './TransactionsList'
import { TransactionsScreenSkeleton } from './TransactionsScreenSkeleton'

export default function TransactionsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions')

  const isLoading = useAppSelector(selectIsTransactionsLoading)
  const transactions = useAppSelector(selectTransactions)
  const isLast = useAppSelector(selectTransactionsIsLast)

  const { appliedFiltersRef, isDirty, ...props } = useTransactionsFilters()

  useEffect(() => {
    return () => {
      dispatch(clearTransactionsState())
    }
  }, [dispatch])

  return (
    <ScreenContent title={translate('title')}>
      <Stack spacing={1} maxWidth={'800px'}>
        <Stack spacing={2}>
          <SearchBar<Transaction>
            apiFunc={transactionsMock.searchTransactions}
            getOptionLabel={(option) => option.name}
            renderOption={(props, option) => (
              <TransactionLine {...props} key={option.transactionId} transaction={option} />
            )}
          />

          <TransactionsFiltersBlock
            {...props}
            appliedFiltersRef={appliedFiltersRef}
            isDirty={isDirty()}
          />
        </Stack>

        {transactions.length === 0 && !isLoading && (
          <EmptyList
            reasonTitle={translate('noTransactions')}
            reasonSubtitle={translate('noTransactionsSubtitle')}
          />
        )}

        {transactions.length > 0 && (
          <TransactionsList
            isLast={isLast}
            isLoading={isLoading}
            transactions={transactions}
            appliedFiltersRef={appliedFiltersRef}
          />
        )}

        {transactions.length === 0 && isLoading && <TransactionsScreenSkeleton />}
      </Stack>
    </ScreenContent>
  )
}
