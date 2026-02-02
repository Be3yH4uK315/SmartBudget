import { Transaction, TransactionsFilters } from '@features/transactions/types'
import { api } from '@shared/api'

class TransactionsApi {
  baseUrl = '/transactions'

  async getTransactions(offset: number, filters?: TransactionsFilters): Promise<Transaction[]> {
    const url = `${this.baseUrl}`

    const params: Record<string, string> = {
      offset: String(offset),
      ...(filters?.categoryIds?.length ? { categoryId: filters.categoryIds.join(',') } : {}),
      ...(filters?.dateFrom ? { dateFrom: filters.dateFrom } : {}),
      ...(filters?.dateTo ? { dateTo: filters.dateTo } : {}),
      ...(filters?.type ? { type: filters.type } : {}),
      ...(filters?.valueFrom !== undefined ? { valueFrom: String(filters.valueFrom) } : {}),
      ...(filters?.valueTo !== undefined ? { valueTo: String(filters.valueTo) } : {}),
    }

    const response = await api.get<Transaction[]>(url, { params })

    return response.data
  }

  async changeCategory(payload: Pick<Transaction, 'categoryId' | 'transactionId'>): Promise<void> {
    const url = `${this.baseUrl}/edit/${payload.transactionId}`
    const response = await api.patch(url, payload.categoryId)

    return response.data
  }
}

export const transactionsApi = new TransactionsApi()
