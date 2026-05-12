import { PAGE_SIZE } from '@features/transactions/constants'
import { Category, Transaction, TransactionsFilters } from '@features/transactions/types'
import { SEARCH_LIMIT } from '@shared/constants'
import dayjs from 'dayjs'

function generateMockTransactions(total = 600): Transaction[] {
  const result: Transaction[] = []
  const statuses = ['confirmed', 'rejected', 'pending'] as const
  const types = ['income', 'expense'] as const
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

  for (let i = 0; i < total; i++) {
    result.push({
      transactionId: `tx_${i}_${Math.random().toString(36).slice(2, 8)}`,
      amount: Math.round(Math.random() * 5000),
      categoryId: ((i % 5) + 1) as Category,
      description: `Описание #${i}`,
      merchant: `Операция #${i}`,
      mcc: `${1000 + (i % 500)}`,
      status: statuses[i % statuses.length],
      transactionType: types[i % types.length],
      date: dates[i % dates.length],
    })
  }

  return result
}

const ALL_TRANSACTIONS: Transaction[] = generateMockTransactions(10000).sort((a, b) =>
  dayjs(a.date).isAfter(dayjs(b.date)) ? -1 : 1,
)

class TransactionsMock {
  baseUrl = '/transactions'
  private data: Transaction[] = ALL_TRANSACTIONS
  private searchRequestId = 0

  private delay(ms = 500) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  private applyFilters(items: Transaction[], filters?: TransactionsFilters) {
    if (!filters) return items

    let res = [...items]

    if (filters.categoryIds?.length) {
      const set = new Set(filters.categoryIds.map(Number))
      res = res.filter((t) => set.has(t.categoryId))
    }

    if (filters.type !== '') res = res.filter((t) => t.transactionType === filters.type)
    if (filters.valueFrom !== undefined) res = res.filter((t) => t.amount >= filters.valueFrom!)
    if (filters.valueTo !== undefined) res = res.filter((t) => t.amount <= filters.valueTo!)
    if (filters.dateFrom) res = res.filter((t) => t.date >= filters.dateFrom)
    if (filters.dateTo) res = res.filter((t) => t.date <= filters.dateTo)

    return res
  }

  async getTransactions(offset: number, filters?: TransactionsFilters): Promise<Transaction[]> {
    console.log('%cMOCK CALL getTransactions', 'color: orange', { offset, ...filters })
    await this.delay(500)

    const filtered = this.applyFilters(this.data, filters)
    return filtered.slice(offset, offset + PAGE_SIZE)
  }

  searchTransactions = async (
    query: string,
    signal: AbortSignal,
    limit: number,
  ): Promise<Transaction[]> => {
    console.log('%cMOCK CALL searchTransactions', 'color: orange', { query })
    const requestId = ++this.searchRequestId

    await this.delay(400)

    if (signal?.aborted) return []

    if (requestId !== this.searchRequestId) return []

    const normalizedQuery = query.trim().toLowerCase()
    if (!normalizedQuery) return []

    return this.data
      .filter(
        (t) =>
          t.merchant.toLowerCase().includes(normalizedQuery) ||
          t.description?.toLowerCase().includes(normalizedQuery) ||
          t.mcc?.includes(normalizedQuery),
      )
      .slice(0, SEARCH_LIMIT)
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
