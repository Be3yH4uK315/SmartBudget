import { api } from '@shared/api'
import { VAPID_PUBLIC_KEY } from '@shared/constants'
import { urlBase64ToUint8Array } from '@shared/utils'

class PushApi {
  baseURL = '/push'

  async requestPermission(): Promise<void> {
    const permission = await Notification.requestPermission()
    if (permission !== 'granted') {
      throw new Error('Notification permission denied')
    }
  }

  async subscribe(): Promise<PushSubscription> {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
    })
    return subscription
  }

  async enablePushNotifications(userId: string): Promise<void> {
    await this.requestPermission()

    const subscription = await this.subscribe()

    await api.post(`${this.baseURL}/subscribe`, {
      userId,
      subscription,
    })
  }

  async unsubscribe(userId: string): Promise<void> {
    const registration = await navigator.serviceWorker.ready
    const subscription = await registration.pushManager.getSubscription()

    if (subscription) {
      await subscription.unsubscribe()
      await api.post(`${this.baseURL}/unsubscribe`, { userId, endpoint: subscription.endpoint })
    }
  }
}

export const pushApi = new PushApi()
