import { DEFAULT_DURATION } from '@shared/constants/toast'
import { store } from '@shared/store'
import { addToast, removeToast } from '@shared/store/toast'
import { ToastOptions } from '@shared/types'

export function closeToast(id: number) {
  store.dispatch(removeToast(id))
}

export function showToast(toast: Omit<ToastOptions, 'id'>) {
  const id = generateId()
  const duration = toast.duration ?? DEFAULT_DURATION[toast.type]
  store.dispatch(addToast({ id, ...toast, duration }))

  if (duration > 0) {
    setTimeout(() => {
      closeToast(id)
    }, duration)
  }
}

export const generateId = (() => {
  let id = 0

  return () => {
    id++
    return id
  }
})()
