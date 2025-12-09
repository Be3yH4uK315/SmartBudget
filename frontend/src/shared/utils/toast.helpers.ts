import { store } from '@shared/store'
import { addToast, removeToast } from '@shared/store/toast'

export function closeToast(id: number) {
  store.dispatch(removeToast(id))
}

export function showToast(toast: Omit<ToastOptions, 'id'>) {
  const id = generateId()
  store.dispatch(addToast({ id, ...toast }))

  if (toast.duration && toast.duration > 0) {
    setTimeout(() => {
      closeToast(id)
    }, toast.duration)
  }
}

export const generateId = (() => {
  let id = 0

  return () => {
    id++
    return id
  }
})()