import { useCallback, useMemo } from 'react'
import 'dayjs/locale/ru'
import { getTransactions } from '@features/transactions/store'
import { TransactionsBlock, TransactionsFilters } from '@features/transactions/types'
import { normalizeBlocksList } from '@features/transactions/utils'
import { Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import dayjs from 'dayjs'
import { GroupedVirtuoso } from 'react-virtuoso'
import { TransactionLine } from './TransactionLine'
import { ListFooter, MUIComponents } from './TransactionsListComponents'

type Props = {
  isLast: boolean
  isLoading: boolean
  transactions: TransactionsBlock[]
  appliedFiltersRef: React.RefObject<TransactionsFilters>
}

export const TransactionsList = ({ isLast, isLoading, transactions, appliedFiltersRef }: Props) => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions')

  const normalizedBlocks = useMemo(() => normalizeBlocksList(transactions), [transactions])

  const filters = appliedFiltersRef.current

  const loadMore = useCallback(() => {
    dispatch(getTransactions(filters))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch])

  const formatGroupDate = (inputDate: string) => {
    const date = dayjs(inputDate)

    if (date.isSame(dayjs(), 'day')) return translate('today')
    if (date.isSame(dayjs().subtract(1, 'day'), 'day')) return translate('yesterday')

    return date.format('D MMMM')
  }

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
        <Typography variant="h4">{formatGroupDate(normalizedBlocks.groups[index])}</Typography>
      )}
      itemContent={(index) => (
        <TransactionLine transaction={normalizedBlocks.transactions[index]} />
      )}
    />
  )
}
