import { Transaction, TransactionsBlock } from '@features/transactions/types'

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
