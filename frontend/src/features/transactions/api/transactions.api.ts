import { PAGE_SIZE } from '@features/transactions/constants'
import { Transaction, TransactionsFilters } from '@features/transactions/types'
import { api } from '@shared/api'
import { SEARCH_LIMIT } from '@shared/constants'

class TransactionsApi {
  baseUrl = '/transactions'

  async getTransactions(offset: number, filters?: TransactionsFilters): Promise<Transaction[]> {
    const url = `${this.baseUrl}`

    const params: Record<string, string> = {
      offset: String(offset),
      limit: String(PAGE_SIZE),
      ...(filters?.categoryIds?.length ? { categoryId: filters.categoryIds.join(',') } : {}),
      ...(filters?.dateFrom ? { occurredFrom: filters.dateFrom } : {}),
      ...(filters?.dateTo ? { occurredTo: filters.dateTo } : {}),
      ...(filters?.type ? { transactionType: filters.type } : {}),
      ...(filters?.valueFrom !== undefined ? { amountFrom: String(filters.valueFrom) } : {}),
      ...(filters?.valueTo !== undefined ? { amountTo: String(filters.valueTo) } : {}),
    }

    const response = await api.get<Transaction[]>(url, { params })

    return response.data
  }

  searchTransactions = async (
    query: string,
    signal: AbortSignal,
    limit?: number,
  ): Promise<Transaction[]> => {
    const url = `${this.baseUrl}/search`

    const params: Record<string, string> = {
      limit: limit ? String(limit) : String(SEARCH_LIMIT),
      query: query,
    }

    const response = await api.get<Transaction[]>(url, { params, signal })

    return response.data
  }

  async changeCategory(payload: Pick<Transaction, 'categoryId' | 'transactionId'>): Promise<void> {
    const url = `${this.baseUrl}/edit/${payload.transactionId}`
    const response = await api.patch(url, payload.categoryId)

    return response.data
  }
}

export const transactionsApi = new TransactionsApi()
