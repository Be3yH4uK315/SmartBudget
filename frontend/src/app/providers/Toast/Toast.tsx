import { forwardRef, type ReactNode } from 'react'
import {
  CheckCircleOutlineOutlined,
  CloseOutlined,
  ErrorOutlineOutlined,
  HighlightOffOutlined,
} from '@mui/icons-material'
import { Alert, AlertColor, AlertTitle, Typography } from '@mui/material'
import { SnackbarContent } from 'notistack'

export const Toast = forwardRef<
  HTMLDivElement,
  ToastOptions & {
    onClose?: () => void
  }
>(({ type, title, message, onClose }, ref) => {
  return (
    <SnackbarContent ref={ref}>
      <Alert
        severity={type}
        iconMapping={iconMapping}
        action={
          <CloseOutlined
            onClick={onClose}
            sx={{
              color: 'gray.main',
              cursor: 'pointer',
              ':hover': {
                color: 'text.primary',
              },
            }}
          />
        }
        sx={{ alignItems: 'center' }}
      >
        <AlertTitle>{title}</AlertTitle>

        {message && <Typography variant="caption">{message}</Typography>}
      </Alert>
    </SnackbarContent>
  )
})

const iconMapping: Partial<Record<AlertColor, ReactNode>> = {
  success: <CheckCircleOutlineOutlined sx={{ fontSize: '32px' }} />,
  info: <ErrorOutlineOutlined sx={{ fontSize: '32px' }} />,
  warning: <ErrorOutlineOutlined sx={{ fontSize: '32px' }} />,
  error: <HighlightOffOutlined sx={{ fontSize: '32px' }} />,
}
