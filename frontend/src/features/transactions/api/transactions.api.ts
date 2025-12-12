import { TempAddPayload, Transaction } from '@features/transactions/types'
import { api } from '@shared/api'

class TransactionsApi {
  baseUrl = '/transactions'

  async getTransactions(offset: number): Promise<Transaction[]> {
    const url = `${this.baseUrl}/?offset=${offset}`
    const response = await api.get<Transaction[]>(url)

    return response.data
  }

  async changeCategory(data: { userId: string; payload: Transaction }): Promise<void> {
    const url = `${this.baseUrl}/id`
    const response = await api.patch(url, data)

    return response.data
  }

  /** Временный эндпоинт для тестов */
  async addTransaction(payload: TempAddPayload): Promise<{ transactionId: string }> {
    const url = `${this.baseUrl}/manual`
    const response = await api.post<{ transactionId: string }>(url, payload)

    return response.data
  }

  /** Временный эндпоинт для тестов */
  async deleteTransaction(transactionId: string): Promise<number> {
    const url = `${this.baseUrl}/?id=${transactionId}`
    const response = await api.delete<Transaction[]>(url)

    return response.status
  }
}

export const transactionsApi = new TransactionsApi()
