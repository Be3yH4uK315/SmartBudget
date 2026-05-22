import { useEffect } from 'react'
import { transactionsApi } from '@features/transactions/api'
import { useTransactionsFilters } from '@features/transactions/hooks'
import {
  clearTransactionsState,
  importTransaction,
  selectIsImportLoading,
  selectIsTransactionsLoading,
  selectTransactions,
  selectTransactionsIsLast,
} from '@features/transactions/store'
import { Transaction } from '@features/transactions/types'
import { Button, Stack } from '@mui/material'
import { EmptyList, ScreenContent, SearchBar, withAuth } from '@shared/components'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { TransactionsFiltersBlock } from './TransactionsFilters'
import { TransactionLine, TransactionsList } from './TransactionsList'
import { TransactionsScreenSkeleton } from './TransactionsScreenSkeleton'

export default function TransactionsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions')

  const isLoading = useAppSelector(selectIsTransactionsLoading)
  const transactions = useAppSelector(selectTransactions)
  const isLast = useAppSelector(selectTransactionsIsLast)
  const isImportLoading = useAppSelector(selectIsImportLoading)

  const { appliedFiltersRef, isDirty, ...props } = useTransactionsFilters()

  const handleImport = async () => {
    await dispatch(importTransaction())
      .unwrap()
      .then(() => {
        dispatch(clearTransactionsState())
        props.applyFilters(appliedFiltersRef.current)
      })
  }

  useEffect(() => {
    return () => {
      dispatch(clearTransactionsState())
    }
  }, [dispatch])

  return (
    <ScreenContent title={translate('title')}>
      <Stack spacing={2} maxWidth={'800px'}>
        <Stack spacing={2}>
          <SearchBar<Transaction>
            apiFunc={transactionsApi.searchTransactions}
            getOptionLabel={(option) => option.merchant}
            renderOption={(props, option) => (
              <TransactionLine {...props} key={option.transactionId} transaction={option} />
            )}
          />

          <Stack direction={'row'} spacing={2} sx={{ alignItems: 'stretch' }}>
            <Button
              variant="yellow"
              onClick={() =>
                dispatch(
                  openModal({
                    id: MODAL_IDS.TRANSACTION_ADD_MODAL,
                    props: {
                      onSuccess: () => {
                        dispatch(clearTransactionsState())
                        props.applyFilters(appliedFiltersRef.current)
                      },
                    },
                  }),
                )
              }
              sx={{ flex: 1 }}
            >
              {translate('createTransaction')}
            </Button>

            <Button
              variant="yellow"
              disabled={isImportLoading}
              onClick={handleImport}
              sx={{ flex: 1 }}
            >
              {translate('importTransactions')}
            </Button>
          </Stack>

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
