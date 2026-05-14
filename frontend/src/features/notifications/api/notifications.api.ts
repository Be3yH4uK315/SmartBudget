import { NOTIFICATIONS_LIMIT } from '@features/notifications/constants'
import { NotificationsFilters, NotificationsListResponse } from '@features/notifications/types'
import { Transaction } from '@features/transactions/types'
import { api } from '@shared/api'

class NotificationsApi {
  baseUrl = '/notifications'
  transactionsUrl = '/transactions'

  async getNotifications(
    offset: number,
    filters: NotificationsFilters,
  ): Promise<NotificationsListResponse> {
    const url = `${this.baseUrl}`

    const params: Record<string, string> = {
      offset: String(offset),
      limit: String(NOTIFICATIONS_LIMIT),
      ...(filters?.services?.length > 0 ? { services: filters.services.join(',') } : {}),
      ...(filters?.statuses?.length > 0 ? { statuses: filters.statuses } : {}),
      ...(filters?.types?.length > 0 ? { types: filters.types.join(',') } : {}),
    }

    const response = await api.get<NotificationsListResponse>(url, { params })
    return response.data
  }

  async getTransactionById(transactionId: string): Promise<Transaction> {
    const url = `${this.transactionsUrl}/${transactionId}`

    const response = await api.get<Transaction>(url)
    return response.data
  }

  async markAsRead(notificationId: string): Promise<void> {
    const url = `${this.baseUrl}/${notificationId}`

    const response = await api.patch<void>(url)
    return response.data
  }

  async markAllAsRead(): Promise<void> {
    const url = `${this.baseUrl}/read-all`

    const response = await api.patch<void>(url)
    return response.data
  }
}

export const notificationsApi = new NotificationsApi()
