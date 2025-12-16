import { Transaction } from '@features/transactions/types'
function generateMockTransactions(total = 60): Transaction[] {
  const result: Transaction[] = []
  const statuses = ['confirmed', 'rejected', 'pending'] as const

  const dates = [
    '2025-12-12T12:12:12',
    '2025-12-11T12:12:12',
    '2025-12-10T12:12:12',
    '2025-12-09T12:12:12',
    '2025-12-08T12:12:12',
    '2025-12-07T12:12:12',
    '2025-12-06T12:12:12',
    '2025-12-05T12:12:12',
    '2025-12-04T12:12:12',
    '2025-12-03T12:12:12',
    '2025-11-29T12:12:12',
    '2025-11-20T12:12:12',
    '2025-11-15T12:12:12',
  ]

  const type = ['income', 'expense'] as const

  for (let i = 0; i < total; i++) {
    const date = dates[i % dates.length]
    result.push({
      transactionId: `tx_${i}_${Math.random().toString(36).slice(2, 8)}`,
      value: Math.round(Math.random() * 5000),
      categoryId: (i % 5) + 1,
      description: `Описание #${i}`,
      name: `Операция #${i}`,
      mcc: `${1000 + (i % 500)}`,
      status: statuses[i % statuses.length],
      type: type[i % type.length],
      date,
    })
  }

  return result
}

const ALL_TRANSACTIONS = generateMockTransactions(1000)

ALL_TRANSACTIONS.sort((a, b) => (a.date > b.date ? -1 : a.date < b.date ? 1 : 0))

class TransactionsMock {
  baseUrl = ''

  async getTransactions(offset: number, categoryId: number | null): Promise<Transaction[]> {
    console.log('%cMOCK CALL offset=' + offset, 'color: orange')
    console.log(categoryId)

    await new Promise((resolve) => setTimeout(resolve, 1000))

    const PAGE_SIZE = 10
    return ALL_TRANSACTIONS.slice(offset, offset + PAGE_SIZE)
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async changeCategory(payload: any): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }
}

export const transactionsMock = new TransactionsMock()
