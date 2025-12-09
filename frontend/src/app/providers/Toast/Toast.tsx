import { ReactNode } from 'react'
import {
  CheckCircleOutlineOutlined,
  CloseOutlined,
  ErrorOutlineOutlined,
  HighlightOffOutlined,
} from '@mui/icons-material'
import { Alert, AlertColor, AlertTitle, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { ToastOptions } from '@shared/types'
import { SnackbarContent } from 'notistack'

type Props = Omit<ToastOptions, 'id'> & {
  onClose?: () => void
}

export const Toast = ({ type, titleKey, messageKey, onClose }: Props) => {
  const translate = useTranslate('Toasts')
  return (
    <SnackbarContent>
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
        <AlertTitle>{translate(titleKey ? titleKey : type)}</AlertTitle>

        {messageKey && (
          <Typography variant="caption">{translate(`message.${messageKey}`)}</Typography>
        )}
      </Alert>
    </SnackbarContent>
  )
}

const iconMapping: Partial<Record<AlertColor, ReactNode>> = {
  success: <CheckCircleOutlineOutlined sx={{ fontSize: '32px' }} />,
  info: <ErrorOutlineOutlined sx={{ fontSize: '32px' }} />,
  warning: <ErrorOutlineOutlined sx={{ fontSize: '32px' }} />,
  error: <HighlightOffOutlined sx={{ fontSize: '32px' }} />,
}
