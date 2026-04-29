import { App } from '@app'
import { createRoot } from 'react-dom/client'

const container = document.getElementById('root')

if (container) {
  const root = createRoot(container)
  root.render(<App />)
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/serviceWorker.js')
      .then(() => console.log('SW registered'))
      .catch(console.error)
  })
}
