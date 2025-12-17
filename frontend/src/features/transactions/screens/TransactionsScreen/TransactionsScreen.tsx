import { useEffect } from 'react'
import { useCategoryFilter } from '@features/transactions/hooks/useCategoryFilter'
import {
  clearTransactionsState,
  getTransactions,
  selectIsTransactionsLoading,
  selectTransactions,
  selectTransactionsIsLast,
} from '@features/transactions/store'
import { CancelOutlined } from '@mui/icons-material'
import { Box, Paper, Stack, Typography } from '@mui/material'
import { withAuth } from '@shared/components'
import { ScreenContent } from '@shared/components/ScreenContent'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { CategoryFilter } from './CategoryFilter'
import { TransactionsList } from './TransactionList'
import { TransactionsScreenSkeleton } from './TransactionsScreenSkeleton'

export default withAuth(function TransactionsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions')

  const isLoading = useAppSelector(selectIsTransactionsLoading)
  const transactions = useAppSelector(selectTransactions)
  const isLast = useAppSelector(selectTransactionsIsLast)

  const { selectedCategory, parsedCategoryId, handleCategoryChange, setSelectedCategory } =
    useCategoryFilter()

  useEffect(() => {
    dispatch(clearTransactionsState())

    if (selectedCategory) {
      dispatch(getTransactions({ categoryId: selectedCategory }))
    } else {
      dispatch(getTransactions({}))
    }
  }, [dispatch, selectedCategory])

  useEffect(() => {
    setSelectedCategory(Number.isFinite(parsedCategoryId) ? parsedCategoryId : null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [parsedCategoryId])

  useEffect(() => {
    return () => {
      dispatch(clearTransactionsState())
    }
  }, [dispatch])

  return (
    <ScreenContent
      title={translate('title')}
      isLoading={isLoading && transactions.length === 0}
      ContentSkeleton={TransactionsScreenSkeleton}
    >
      {transactions.length === 0 && (
        <Paper
          sx={{
            p: 4,
            maxWidth: '800px',
            bgcolor: 'surface.light',
            minHeight: '400px',
            borderRadius: '32px',
          }}
        >
          <Stack
            spacing={1}
            sx={{
              height: '100%',
              borderStyle: 'dashed',
              borderColor: 'primary.main',
              borderWidth: '2px',
              justifyContent: 'center',
              alignItems: 'center',
              borderRadius: '24px',
            }}
          >
            <Box sx={{ borderRadius: '24px', lineHeight: 0, p: 2, m: 0, bgcolor: 'error.light' }}>
              <CancelOutlined sx={{ width: '50px', height: '50px', color: 'error.main' }} />
            </Box>

            <Typography variant="h3">{translate('noTransactions')}</Typography>
          </Stack>
        </Paper>
      )}

      {transactions.length > 0 && (
        <>
          <CategoryFilter onChange={handleCategoryChange} selectedCategory={selectedCategory} />

          <TransactionsList
            isLast={isLast}
            isLoading={isLoading}
            transactions={transactions}
            selectedCategory={selectedCategory}
          />
        </>
      )}
    </ScreenContent>
  )
})
