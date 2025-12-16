import { TempAddPayload, Transaction } from '@features/transactions/types'
import { api } from '@shared/api'

class TransactionsApi {
  baseUrl = '/transactions'

  async getTransactions(offset: number): Promise<Transaction[]> {
    const url = `${this.baseUrl}/?offset=${offset}`
    const response = await api.get<Transaction[]>(url)

    return response.data
  }

  async changeCategory(payload: Pick<Transaction, 'categoryId' | 'transactionId'>): Promise<void> {
    const url = `${this.baseUrl}/edit/${payload.transactionId}`
    const response = await api.patch(url, payload.categoryId)

    return response.data
  }

  /** Временный эндпоинт для тестов */
  async addTransaction(payload: TempAddPayload): Promise<{ transactionId: string }> {
    const url = `${this.baseUrl}/edit`
    const response = await api.post<{ transactionId: string }>(url, payload)

    return response.data
  }

  /** Временный эндпоинт для тестов */
  async deleteTransaction(transactionId: string): Promise<number> {
    const url = `${this.baseUrl}/edit/${transactionId}`
    const response = await api.delete<Transaction[]>(url)

    return response.status
  }
}

export const transactionsApi = new TransactionsApi()
