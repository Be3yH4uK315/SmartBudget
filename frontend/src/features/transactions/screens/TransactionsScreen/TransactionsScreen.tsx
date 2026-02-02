import { useEffect } from 'react'
import {
  clearTransactionsState,
  getTransactions,
  selectIsTransactionsLoading,
  selectTransactions,
  selectTransactionsFilters,
  selectTransactionsIsLast,
  setCategoryIds,
} from '@features/transactions/store'
import { parseCategoryIds } from '@features/transactions/utils'
import { Stack } from '@mui/material'
import { EmptyList, ScreenContent, withAuth } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { useSearchParams } from 'react-router'
import { TransactionsFiltersBlock } from './TransactionsFilters'
import { TransactionsList } from './TransactionsList'
import { TransactionsScreenSkeleton } from './TransactionsScreenSkeleton'

export default function TransactionsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions')
  const [searchParams] = useSearchParams()

  const isLoading = useAppSelector(selectIsTransactionsLoading)
  const transactions = useAppSelector(selectTransactions)
  const isLast = useAppSelector(selectTransactionsIsLast)
  const filters = useAppSelector(selectTransactionsFilters)

  useEffect(() => {
    const categoryParam = searchParams.get('categoriesIds')
    const ids = parseCategoryIds(categoryParam?.split(',') ?? [])

    if (categoryParam !== null) {
      dispatch(setCategoryIds(ids))
    }

    dispatch(getTransactions())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    return () => {
      dispatch(clearTransactionsState())
    }
  }, [dispatch])

  return (
    <ScreenContent title={translate('title')}>
      <Stack spacing={1} maxWidth={'800px'}>
        <TransactionsFiltersBlock filters={filters} />

        {transactions.length === 0 && !isLoading && (
          <EmptyList
            reasonTitle={translate('noTransactions')}
            reasonSubtitle={translate('noTransactionsSubtitle')}
          />
        )}

        {transactions.length > 0 && (
          <TransactionsList isLast={isLast} isLoading={isLoading} transactions={transactions} />
        )}

        {transactions.length === 0 && isLoading && <TransactionsScreenSkeleton />}
      </Stack>
    </ScreenContent>
  )
}
