import { PropsWithChildren } from 'react'
import { Box } from '@mui/material'
import { selectUser, useAppSelector } from '@shared/store'
import { Header } from './Header'

export const RootLayout = ({ children }: PropsWithChildren) => {
  const isAuth = useAppSelector(selectUser).isAuth

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'surface.main',
      }}
    >
      {!isAuth && <Header />}

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
