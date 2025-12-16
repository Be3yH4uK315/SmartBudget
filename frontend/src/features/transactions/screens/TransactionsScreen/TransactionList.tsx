import { useCallback, useMemo } from 'react'
import 'dayjs/locale/ru'
import { ListFooter, MUIComponents } from '@features/transactions/components'
import { getTransactions } from '@features/transactions/store'
import { TransactionsBlock } from '@features/transactions/types'
import { normalizeBlocksList } from '@features/transactions/utils'
import { Typography } from '@mui/material'
import { useAppDispatch } from '@shared/store'
import dayjs from 'dayjs'
import { GroupedVirtuoso } from 'react-virtuoso'
import { TransactionLine } from './TransactionLine'

type Props = {
  isLast: boolean
  isLoading: boolean
  transactions: TransactionsBlock[]
}

export const TransactionsList = ({ isLast, isLoading, transactions }: Props) => {
  const dispatch = useAppDispatch()

  const normalizedBlocks = useMemo(() => normalizeBlocksList(transactions), [transactions])

  const loadMore = useCallback(() => {
    dispatch(getTransactions())
  }, [dispatch])

  return (
    <GroupedVirtuoso
      style={{ height: '100%' }}
      components={{
        ...MUIComponents,
        Footer: () => <ListFooter isLast={isLast} isLoading={isLoading} />,
      }}
      useWindowScroll
      increaseViewportBy={{ bottom: 400, top: 0 }}
      overscan={200}
      groupCounts={normalizedBlocks.groupCounts}
      endReached={() => (!isLoading && !isLast ? loadMore() : null)}
      groupContent={(index) => (
        <Typography variant="h4">
          {dayjs(normalizedBlocks.groups[index]).locale('ru').format('D MMMM')}
        </Typography>
      )}
      itemContent={(index) => (
        <TransactionLine transaction={normalizedBlocks.transactions[index]} />
      )}
    />
  )
}
