import { AriaRole, ReactNode } from 'react'
import { Paper, SxProps } from '@mui/material'

type Props = {
  children?: ReactNode
  paperSx?: SxProps
  noElevation?: boolean
  onClick?: () => void
  role?: AriaRole
}

export const StyledPaper = ({
  children,
  paperSx,
  noElevation = false,
  onClick,
  role = 'div',
}: Props) => {
  return (
    <Paper
      role={role}
      onClick={onClick}
      elevation={noElevation ? 0 : 2}
      sx={{
        px: 3,
        py: 2,
        height: 'max-content',
        borderRadius: '24px',
        display: 'flex',
        flexDirection: 'column',
        mx: 0,
        ...paperSx,
      }}
    >
      {children}
    </Paper>
  )
}
