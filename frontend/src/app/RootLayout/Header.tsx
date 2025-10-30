import { useMemo } from 'react'
import { LogoutRounded } from '@mui/icons-material'
import { AppBar, Box, Button, Container, Tab, Tabs } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { Link as RouterLink, useLocation } from 'react-router'

export default function Header() {
  const { pathname } = useLocation()
  const translate = useTranslate('HeaderTabs')

  const routes = useMemo(
    () => [
      { label: translate('main'), to: '/' },
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
          value={value}
          TabIndicatorProps={{ sx: { bgcolor: 'primary.main' } }}
          aria-label="main navigation"
        >
          {routes.map((r) => (
            <Tab key={r.to} label={r.label} component={RouterLink} to={r.to} disableRipple />
          ))}
        </Tabs>

        <Box sx={{ flexGrow: 1 }} />

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
      </Container>
    </AppBar>
  )
}
