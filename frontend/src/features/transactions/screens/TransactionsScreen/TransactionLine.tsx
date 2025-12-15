import React from 'react'
import { CategoryIcon } from '@features/transactions/components'
import { Transaction } from '@features/transactions/types'
import { Box, Stack, Typography } from '@mui/material'
import { useTheme, useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { formatCurrency } from '@shared/utils'

type Props = {
  transaction: Transaction
}

export const TransactionLine = React.memo(function TransactionLine({ transaction }: Props) {
  const translate = useTranslate('Transactions')
  const translateCategory = useTranslate('Categories')
  const dispatch = useAppDispatch()
  const theme = useTheme()

  const handleClick = () =>
    dispatch(
      openModal({ id: 'transactionInfo', props: { transactionId: transaction.transactionId } }),
    )

  const color =
    transaction.status === 'pending'
      ? 'gray.main'
      : transaction.type === 'income'
        ? 'success.main'
        : 'text.primary'

  const iconBgColor = theme.colorMode === 'light' ? 'gray.light' : 'surface.light'
  const iconColor = theme.colorMode === 'light' ? 'gray.dark' : 'text.primary'

  return (
    <Box
      sx={{ display: 'flex', width: '100%', justifyContent: 'space-between' }}
      onClick={handleClick}
    >
      <Stack direction={'row'} spacing={2} alignItems={'center'}>
        <CategoryIcon
          categoryId={transaction.categoryId}
          size={48}
          boxSx={{ p: 1, width: 'max-content', height: 'max-content', bgcolor: iconBgColor }}
          iconSx={{ color: iconColor }}
        />

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
