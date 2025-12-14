import React from 'react'
import 'dayjs/locale/ru'
import { TransactionsBlock } from '@features/transactions/types'
import { Stack, Typography } from '@mui/material'
import dayjs from 'dayjs'
import { TransactionLine } from './TransactionLine'

type Props = {
  transactions: TransactionsBlock
}
export const TransactionsInBlock = React.memo(function TransactionsInBlock({
  transactions,
}: Props) {
  return (
    <Stack spacing={2}>
      <Typography variant="h4">{dayjs(transactions.date).locale('ru').format('D MMMM')}</Typography>

      <Stack spacing={1}>
        {transactions.transactions.map((t) => (
          <TransactionLine key={t.transactionId} transaction={t} />
        ))}
      </Stack>
    </Stack>
  )
})
