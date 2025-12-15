import { TransactionsBlock } from '@features/transactions/types'

type Props = {
  currentBlocks: TransactionsBlock[]
  newBlocks: TransactionsBlock[]
}

export function mergeTransactionBlocks({ currentBlocks, newBlocks }: Props): TransactionsBlock[] {
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
