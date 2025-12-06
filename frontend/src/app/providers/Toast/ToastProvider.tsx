import { createContext, PropsWithChildren, useCallback, useEffect, useState } from 'react'
import { SnackbarProvider } from 'notistack'
import { setShowToast } from './globalToast'
import { Toast } from './Toast'

export const ToastContext = createContext({ showToast: (t: ToastOptions) => {} })

export const ToastProvider = ({ children }: PropsWithChildren) => {
  const [toast, setToast] = useState<ToastOptions | null>(null)

  const showToast = useCallback((toast: ToastOptions) => {
    setToast(toast)
  }, [])

  const closeToast = useCallback(() => {
    setToast(null)
  }, [])

  useEffect(() => {
    setShowToast(showToast)
    return () => setShowToast(() => {})
  }, [showToast])

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
