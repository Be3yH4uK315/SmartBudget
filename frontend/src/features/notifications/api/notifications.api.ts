import { NOTIFICATIONS_LIMIT } from '@features/notifications/constants'
import { Notification } from '@features/notifications/types'
import { Transaction } from '@features/transactions/types'
import { api } from '@shared/api'

class NotificationsApi {
  baseUrl = '/notifications'

  async getNotifications(offset: number): Promise<Notification[]> {
    const url = `${this.baseUrl}`

    const params = {
      limit: NOTIFICATIONS_LIMIT,
      offset,
    }

    const response = await api.get<Notification[]>(url, { params })
    return response.data
  }

  async getTransactionById(transactionId: string): Promise<Transaction> {
    const url = `${this.baseUrl}/transaction/${transactionId}`

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
