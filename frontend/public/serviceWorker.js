self.addEventListener('push', function (event) {
  const pushData = event.data?.json()
  if (!pushData) {
    return
  }

  event.waitUntil(
    (async () => {
      await self.registration.showNotification(pushData.title, {
        body: pushData.body,
        icon: '/icon_192.png',
        data: { url: pushData.url || '/' },
      })
    })(),
  )
})

self.addEventListener('notificationclick', function (event) {
  event.notification.close()

  const url = new URL(event.notification.data?.url || '/', self.location.origin).href

  event.waitUntil(
    self.clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientsArr) => {
        for (const client of clientsArr) {
          if (client.url === url && 'focus' in client) {
            return client.focus()
          }
        }
        return self.clients.openWindow(url)
      })
      .catch((e) => {
        console.error(e)
      }),
  )
})
