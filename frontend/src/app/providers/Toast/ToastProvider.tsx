import { createContext, PropsWithChildren, useCallback, useState } from 'react'
import { SnackbarProvider } from 'notistack'
import { setShowToast } from './globalToast'
import { Toast } from './Toast'

export const ToastContext = createContext<{
  showToast(toast: ToastOptions): void
}>({
  showToast() {},
})

export const ToastProvider = ({ children }: PropsWithChildren) => {
  const [toast, setToast] = useState<ToastOptions | null>(null)

  const showToast = useCallback((toast: ToastOptions) => {
    setToast(toast)
  }, [])

  const closeToast = () => setToast(null)

  setShowToast(showToast)
  return (
    <SnackbarProvider>
      <ToastContext.Provider value={{ showToast }}>
        {children}

        {toast && (
          <Toast
            onClose={closeToast}
            type={toast.type}
            title={toast.title}
            message={toast.message}
          />
        )}
      </ToastContext.Provider>
    </SnackbarProvider>
  )
}
