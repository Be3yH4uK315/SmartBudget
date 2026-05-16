import { PAGE_SIZE } from '@features/transactions/constants'
import {
  GoalId,
  ManualTransaction,
  Transaction,
  TransactionsFilters,
} from '@features/transactions/types'
import { api } from '@shared/api'
import { SEARCH_LIMIT } from '@shared/constants'

class TransactionsApi {
  baseUrl = '/transactions'
  goalsUrl = '/goals'

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
    const url = `${this.baseUrl}/${payload.transactionId}`
    const response = await api.patch<void>(url, { categoryId: payload.categoryId })

    return response.data
  }

  async addTransaction(payload: ManualTransaction): Promise<void> {
    const url = `${this.baseUrl}/manual`
    const response = await api.post<void>(url, payload)

    return response.data
  }

  async importTransaction(): Promise<void> {
    const url = `${this.baseUrl}/import`
    const response = await api.post<void>(url)

    return response.data
  }

  async getGoalsNames(): Promise<GoalId[]> {
    const url = `${this.goalsUrl}/names`
    const response = await api.get<GoalId[]>(url)

    return response.data
  }
}

export const transactionsApi = new TransactionsApi()
