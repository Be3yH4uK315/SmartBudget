import { useMemo } from 'react'
import { LogoutRounded } from '@mui/icons-material'
import { AppBar, Box, Button, Container, IconButton, Tab, Tabs, useMediaQuery } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { Link as RouterLink, useLocation } from 'react-router'

export const Header = () => {
  const { pathname } = useLocation()
  const translate = useTranslate('HeaderTabs')
  const isMobile = useMediaQuery((theme) => theme.breakpoints.down('sm'))

  const routes = useMemo(
    () => [
      { label: translate('main'), to: '/main' },
      { label: translate('budget'), to: '/budget' },
      { label: translate('goals'), to: '/goals' },
      { label: translate('transactions'), to: '/transactions' },
      { label: translate('settings'), to: '/settings' },
    ],
    [translate],
  )

  const value = useMemo(() => {
    const idx = routes.findIndex((r) =>
      r.to === '/' ? pathname === '/' : pathname.startsWith(r.to),
    )
    return idx === -1 ? false : idx
  }, [pathname, routes])

  return (
    <AppBar position="static" color="transparent" sx={{ bgcolor: 'surface.light' }}>
      <Container maxWidth="lg" sx={{ display: 'flex', alignItems: 'center' }}>
        <Tabs
          id="back-to-top-anchor"
          value={value}
          TabIndicatorProps={{ sx: { bgcolor: 'primary.main' } }}
          aria-label="main navigation"
        >
          {routes.map((r) => (
            <Tab
              key={r.to}
              label={r.label}
              component={RouterLink}
              to={r.to}
              disableRipple
              sx={{
                minWidth: 'auto',
                px: { xs: 1, sm: 2 },
              }}
            />
          ))}
        </Tabs>
        <Box sx={{ flexGrow: 1 }} />
        {isMobile && (
          <IconButton
            aria-label={translate('logout')}
            sx={{
              bgcolor: 'transparent',
              '&:hover': { bgcolor: 'transparent' },
              typography: 'caption',
              color: 'secondary.main',
            }}
          >
            <LogoutRounded />
          </IconButton>
        )}

        {!isMobile && (
          <Button
            sx={{
              bgcolor: 'transparent',
              '&:hover': { bgcolor: 'transparent' },
              typography: 'caption',
            }}
            endIcon={<LogoutRounded />}
          >
            {translate('logout')}
          </Button>
        )}
      </Container>
    </AppBar>
  )
}
