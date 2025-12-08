import { store } from '@shared/store'
import { addToast, removeToast } from '@shared/store/toast'

export function closeToast() {
  store.dispatch(removeToast())
}

export function showToast(toast: ToastOptions) {
  store.dispatch(addToast(toast))

  if (toast.duration && toast.duration > 0) {
    setTimeout(() => {
      closeToast()
    }, toast.duration)
  }
}
