import { Category, Transaction, TransactionsFilters } from '@features/transactions/types'

function generateMockTransactions(total = 600): Transaction[] {
  const result: Transaction[] = []
  const statuses = ['confirmed', 'rejected', 'pending'] as const

  const dates = [
    '2026-01-24T12:12:12',
    '2026-01-23T12:12:12',
    '2026-01-21T12:12:12',
    '2026-01-20T12:12:12',
    '2026-01-19T12:12:12',
    '2026-01-18T12:12:12',
    '2026-01-17T12:12:12',
    '2025-12-05T12:12:12',
    '2025-12-04T12:12:12',
    '2025-12-03T12:12:12',
    '2025-11-29T12:12:12',
    '2025-11-20T12:12:12',
    '2025-11-15T12:12:12',
  ]

  const types = ['income', 'expense'] as const

  for (let i = 0; i < total; i++) {
    const date = dates[i % dates.length]

    result.push({
      transactionId: `tx_${i}_${Math.random().toString(36).slice(2, 8)}`,
      value: Math.round(Math.random() * 5000),
      categoryId: ((i % 5) + 1) as Category,
      description: `Описание #${i}`,
      name: `Операция #${i}`,
      mcc: `${1000 + (i % 500)}`,
      status: statuses[i % statuses.length],
      type: types[i % types.length],
      date,
    })
  }

  return result
}

const ALL_TRANSACTIONS: Transaction[] = generateMockTransactions(10000).sort((a, b) =>
  a.date > b.date ? -1 : a.date < b.date ? 1 : 0,
)

class TransactionsMock {
  baseUrl = '/transactions'

  private readonly PAGE_SIZE = 50
  private data: Transaction[] = ALL_TRANSACTIONS

  private delay(ms = 500) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  private applyFilters(items: Transaction[], filters?: TransactionsFilters): Transaction[] {
    if (!filters) return items

    let res = [...items]

    if (filters.categoryIds?.length) {
      const set = new Set(filters.categoryIds)
      res = res.filter((t) => set.has(t.categoryId))
    }

    if (filters.type) {
      res = res.filter((t) => t.type === filters.type)
    }

    if (filters.valueFrom !== undefined) {
      res = res.filter((t) => t.value >= filters.valueFrom!)
    }

    if (filters.valueTo !== undefined) {
      res = res.filter((t) => t.value <= filters.valueTo!)
    }

    // фильтр по датам (включительно)
    if (filters.dateFrom) {
      res = res.filter((t) => t.date >= filters.dateFrom)
    }

    if (filters.dateTo) {
      res = res.filter((t) => t.date <= filters.dateTo)
    }

    return res
  }

  async getTransactions(offset: number, filters?: TransactionsFilters): Promise<Transaction[]> {
    console.log('%cMOCK CALL getTransactions', 'color: orange', { offset, filters })

    await this.delay(500)

    const filtered = this.applyFilters(this.data, filters)

    return filtered.slice(offset, offset + this.PAGE_SIZE)
  }

  async changeCategory(payload: Pick<Transaction, 'categoryId' | 'transactionId'>): Promise<void> {
    console.log('%cMOCK CALL changeCategory', 'color: orange', payload)

    await this.delay(500)

    this.data = this.data.map((t) =>
      t.transactionId === payload.transactionId ? { ...t, categoryId: payload.categoryId } : t,
    )
  }
}

export const transactionsMock = new TransactionsMock()
