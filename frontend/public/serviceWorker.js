self.addEventListener('push', function (event) {
  let data = { title: 'Fallback', body: 'No payload', url: '/' }

  try {
    data = event.data?.json() || data
  } catch {
    console.error('Invalid push payload')
  }

  event.waitUntil(
    (async () => {
      await self.registration.showNotification(data.title, {
        body: data.body,
        icon: '/icon_192.png',
        data: { url: data.url || '/' },
      })
    })(),
  )
})

self.addEventListener('notificationclick', function (event) {
  event.notification.close()

  const url = event.notification.data?.url || '/'

  console.log(url)

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientsArr) => {
      for (const client of clientsArr) {
        if (client.url === url && 'focus' in client) {
          return client.focus()
        }
      }
      return self.clients.openWindow(url)
    }),
  )
})
