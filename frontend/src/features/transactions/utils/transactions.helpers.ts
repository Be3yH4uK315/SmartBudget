import {
  Category,
  Transaction,
  TransactionsBlock,
  TransactionsFilters,
} from '@features/transactions/types'
import { CATEGORY_IDS } from '@shared/constants'
import { isSetsEqual } from '@shared/utils'

type MergeTransactionProps = {
  currentBlocks: TransactionsBlock[]
  newBlocks: TransactionsBlock[]
}

export function mergeTransactionBlocks({
  currentBlocks,
  newBlocks,
}: MergeTransactionProps): TransactionsBlock[] {
  return [
    ...currentBlocks.slice(0, -1),
    {
      ...currentBlocks[currentBlocks.length - 1],
      transactions: [
        ...currentBlocks[currentBlocks.length - 1].transactions,
        ...newBlocks[0].transactions,
      ],
    },
    ...newBlocks.slice(1),
  ]
}

export function groupByDate(transactions: Transaction[]): TransactionsBlock[] {
  return transactions.reduce<TransactionsBlock[]>((blocks, transaction) => {
    const date = transaction.date.split('T')[0]
    const lastBlock = blocks[blocks.length - 1]

    if (lastBlock && lastBlock.date === date) {
      lastBlock.transactions.push(transaction)
    } else {
      blocks.push({
        date: date,
        transactions: [transaction],
      })
    }

    return blocks
  }, [])
}

export function normalizeBlocksList(blocks: TransactionsBlock[]) {
  const groups: string[] = []
  const groupCounts: number[] = []
  const transactions: Transaction[] = []

  for (const block of blocks) {
    groups.push(block.date)
    groupCounts.push(block.transactions.length)
    transactions.push(...block.transactions)
  }

  return { groups, groupCounts, transactions }
}

export function parseCategoryIds(ids: string[]): Category[] {
  return ids.map(Number).filter((n): n is Category => CATEGORY_IDS.includes(n as Category))
}

export function isSameFilters(a: TransactionsFilters, b: TransactionsFilters) {
  return (
    a.type === b.type &&
    a.dateFrom === b.dateFrom &&
    a.dateTo === b.dateTo &&
    a.valueFrom === b.valueFrom &&
    a.valueTo === b.valueTo &&
    isSetsEqual(a.categoryIds, b.categoryIds)
  )
}
