import { Transaction } from '@features/transactions/types'
function generateMockTransactions(total = 60): Transaction[] {
  const result: Transaction[] = []
  const statuses = ['confirmed', 'rejected', 'pending'] as const

  // Даты — несколько дней, чтобы проверить группировку
  const dates = [
    '2025-12-12',
    '2025-12-11',
    '2025-12-10',
    '2025-12-09',
    '2025-11-29',
    '2025-11-20',
    '2025-11-15',
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

const ALL_TRANSACTIONS = generateMockTransactions(11)

// Отсортируем: новые сверху (даты DESC)
ALL_TRANSACTIONS.sort((a, b) => (a.date > b.date ? -1 : a.date < b.date ? 1 : 0))

class TransactionsMock {
  baseUrl = ''

  async getTransactions(offset: number): Promise<Transaction[]> {
    console.log('%cMOCK CALL offset=' + offset, 'color: orange')

    await new Promise((resolve) => setTimeout(resolve, 1000))

    const PAGE_SIZE = 10
    return ALL_TRANSACTIONS.slice(offset, offset + PAGE_SIZE)
  }
}

export const transactionsMock = new TransactionsMock()
