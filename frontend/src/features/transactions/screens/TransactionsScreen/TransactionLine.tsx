import React from 'react'
import { Transaction } from '@features/transactions/types'
import { Box, Stack, Typography } from '@mui/material'
import { TransactionIcon } from '@shared/assets/icons'
import { useTranslate } from '@shared/hooks'
import { formatCurrency } from '@shared/utils'
import { useLocation, useNavigate } from 'react-router'

type Props = {
  transaction: Transaction
}

export const TransactionLine = React.memo(function TransactionLine({ transaction }: Props) {
  const translate = useTranslate('Transactions')
  const translateCategory = useTranslate('Categories')
  const navigate = useNavigate()
  const location = useLocation()

  const color =
    transaction.status === 'pending'
      ? 'gray.main'
      : transaction.type === 'income'
        ? 'success.main'
        : 'text.primary'

  const handleClick = () =>
    navigate(`./${transaction.transactionId}`, { state: { backgroundLocation: location } })

  return (
    <Box display={'flex'} justifyContent={'space-between'} onClick={handleClick}>
      <Stack direction={'row'} spacing={2}>
        <Box
          sx={{
            bgcolor: 'gray.main',
            width: 'max-content',
            height: 'max-content',
            borderRadius: '24px',
            p: 1,
            lineHeight: 0,
            color: '#FFFFFF',
          }}
        >
          {<TransactionIcon />}
        </Box>

        <Stack>
          <Typography variant="h5">{transaction.name}</Typography>

          <Typography variant="caption">{translateCategory(transaction.categoryId)}</Typography>
        </Stack>
      </Stack>

      <Stack textAlign={'right'}>
        <Typography variant="h5" color={color}>
          {formatCurrency(transaction.value, transaction.type)}
        </Typography>

        <Typography variant="caption">{translate('debitCard')}</Typography>
      </Stack>
    </Box>
  )
})
