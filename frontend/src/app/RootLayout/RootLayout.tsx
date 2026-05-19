import { PropsWithChildren } from 'react'
import { Box } from '@mui/material'
import { ROUTES } from '@shared/constants'
import { selectUser, useAppSelector } from '@shared/store'
import { useLocation } from 'react-router'
import { Header } from './Header'
import { PublicHeader } from './PublicHeader'

export const RootLayout = ({ children }: PropsWithChildren) => {
  const { isAuth } = useAppSelector(selectUser)
  const { pathname } = useLocation()

  const isPublicPage = pathname === ROUTES.PAGES.PUBLIC_PAGE

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'surface.main',
      }}
    >
      {isAuth && !isPublicPage && <Header />}
      {!isAuth && isPublicPage && <PublicHeader />}

      <Box
        sx={{
          display: 'flex',
          flex: 1,
          backgroundColor: 'surface.main',
          pb: isPublicPage ? 0 : { xs: 8, sm: 12 },
        }}
      >
        {children}
      </Box>

      {/* footer будет тута */}
    </Box>
  )
}
