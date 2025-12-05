let showToastGlobal: ((toast: ToastOptions) => void) | null = null

export const setShowToast = (fn: (toast: ToastOptions) => void) => {
  showToastGlobal = fn
}

export const showToast = (toast: ToastOptions) => {
  showToastGlobal?.(toast)
}
