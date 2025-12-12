import { useEffect } from 'react'
import {
  getTransactions,
  selectIsTransactionsLoading,
  selectTransactions,
  selectTransactionsIsLast,
} from '@features/transactions/store'
import { CancelOutlined } from '@mui/icons-material'
import { Box, Button, Paper, Stack, Typography } from '@mui/material'
import { ScreenContent } from '@shared/components/ScreenContent'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { TransactionsInBlock } from './TransactionsBlock'
import { TransactionsScreenSkeleton } from './TransactionsScreenSkeleton'

export default function TransactionsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions')

  const isLoading = useAppSelector(selectIsTransactionsLoading)
  const transactions = useAppSelector(selectTransactions)
  const isLast = useAppSelector(selectTransactionsIsLast)

  useEffect(() => {
    if (transactions.length === 0) {
      dispatch(getTransactions())
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch])

  const handleLoadMore = () => {
    if (isLoading || isLast) return
    dispatch(getTransactions())
  }

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
        <Stack spacing={2} maxWidth={'800px'}>
          {transactions.map((t) => (
            <TransactionsInBlock key={t.date} transactions={t} />
          ))}

          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            {isLoading ? (
              <Button variant="yellow" disabled>
                {translate('loading')}
              </Button>
            ) : !isLast ? (
              <Button variant="yellow" onClick={handleLoadMore}>
                {translate('loadMore')}
              </Button>
            ) : null}
          </Box>
        </Stack>
      )}
    </ScreenContent>
  )
}
