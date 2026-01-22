import { ReactNode } from 'react'
import { Box, SxProps } from '@mui/material'

type Props = {
  children: ReactNode
  boxSx?: SxProps
}

export const StyledBox = ({ children, boxSx }: Props) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 1,
        alignItems: 'center',
        ...boxSx,
      }}
    >
      {children}
    </Box>
  )
}
