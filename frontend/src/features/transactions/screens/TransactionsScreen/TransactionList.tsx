import { forwardRef, useCallback, useMemo } from 'react'
import 'dayjs/locale/ru'
import { getTransactions } from '@features/transactions/store'
import { TransactionsBlock } from '@features/transactions/types'
import { normalizeBlocksList } from '@features/transactions/utils'
import { Box, CircularProgress, List, ListItem, Typography } from '@mui/material'
import { useAppDispatch } from '@shared/store'
import dayjs from 'dayjs'
import { GroupedVirtuoso, GroupedVirtuosoProps } from 'react-virtuoso'
import { TransactionLine } from './TransactionLine'

type Props = {
  isLast: boolean
  isLoading: boolean
  transactions: TransactionsBlock[]
}

export const TransactionsList = ({ isLast, isLoading, transactions }: Props) => {
  const dispatch = useAppDispatch()

  const normalizedBlocks = useMemo(() => normalizeBlocksList(transactions), [transactions])

  const MUIComponents: GroupedVirtuosoProps<unknown, unknown>['components'] = {
    List: forwardRef(({ style, children, ...props }, ref) => (
      <List
        ref={ref}
        {...props}
        component="div"
        style={{ ...style }}
        sx={{ padding: 0, margin: 0, maxWidth: '800px' }}
      >
        {children}
      </List>
    )),

    Item: ({ children, ...props }) => (
      <ListItem component={'div'} {...props} sx={{ px: 0, py: 1 }}>
        {children}
      </ListItem>
    ),

    Group: ({ children }) => (
      <Box component={'div'} sx={{ bgcolor: 'surface.main', py: 2 }}>
        {children}
      </Box>
    ),
  }

  const Footer = () => {
    if (!isLast && isLoading) {
      return (
        <Box sx={{ display: 'flex', maxWidth: '800px', justifyContent: 'center', py: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )
    }
  }

  const loadMore = useCallback(() => {
    dispatch(getTransactions())
  }, [dispatch])

  return (
    <GroupedVirtuoso
      style={{ height: '100%' }}
      components={{ ...MUIComponents, Footer }}
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
