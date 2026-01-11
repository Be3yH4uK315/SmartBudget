import { ReactNode } from 'react'
import { Paper, SxProps } from '@mui/material'

type Props = {
  children: ReactNode
  paperSx?: SxProps
  elevation?: number
}

export const StyledPaper = ({ children, paperSx, elevation }: Props) => {
  return (
    <Paper
      elevation={elevation === 0 ? elevation : 2}
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
