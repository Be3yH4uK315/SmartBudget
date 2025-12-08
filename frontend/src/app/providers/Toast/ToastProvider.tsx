import { PropsWithChildren } from 'react'
import { Box } from '@mui/material'
import { useAppSelector } from '@shared/store'
import { selectToasts } from '@shared/store/toast'
import { closeToast } from '@shared/utils'
import { SnackbarProvider } from 'notistack'
import { Toast } from './Toast'

export const ToastProvider = ({ children }: PropsWithChildren) => {
  const toasts = useAppSelector(selectToasts)

  return (
    <SnackbarProvider>
      {children}

      <Box
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          display: 'flex',
          flexDirection: 'column-reverse',
          gap: 1,
          zIndex: 10000,
        }}
      >
        {toasts.map((toast, index) => (
          <Toast
            key={index}
            onClose={closeToast}
            type={toast.type}
            titleKey={toast.titleKey}
            messageKey={toast.messageKey}
          />
        ))}
      </Box>
    </SnackbarProvider>
  )
}
