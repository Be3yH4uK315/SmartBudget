import { PropsWithChildren } from 'react'
import { Box } from '@mui/material'
import { Header } from './Header'

export const RootLayout = ({ children }: PropsWithChildren) => {
  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'surface.main',
      }}
    >
      <Header />

      <Box
        sx={{
          display: 'flex',
          flex: 1,
          backgroundColor: 'surface.main',
          pb: { xs: 8, sm: 12 },
        }}
      >
        {children}
      </Box>

      {/* footer будет тута */}
    </Box>
  )
}
