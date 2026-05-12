import { useMemo, useState } from 'react'
import { LogoutRounded, Menu as MenuIcon } from '@mui/icons-material'
import {
  AppBar,
  Box,
  Button,
  Container,
  IconButton,
  Menu,
  MenuItem,
  Tab,
  Tabs,
  useMediaQuery,
} from '@mui/material'
import { TypographyWithAdornment } from '@shared/components'
import { ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import { logoutHelper } from '@shared/utils'
import { Link as RouterLink, useLocation } from 'react-router'
import { LanguageMenu } from './LanguageMenu'
import { ThemeButton } from './ThemeButton'

export const Header = () => {
  const { pathname } = useLocation()
  const dispatch = useAppDispatch()
  const translate = useTranslate('HeaderTabs')
  const isMobile = useMediaQuery((theme) => theme.breakpoints.down(800))

  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const open = Boolean(anchorEl)

  const routes = useMemo(
    () => [
      { label: translate('main'), to: ROUTES.PAGES.DASHBOARD },
      { label: translate('budget'), to: ROUTES.PAGES.BUDGET },
      { label: translate('goals'), to: ROUTES.PAGES.GOALS.MAIN },
      { label: translate('transactions'), to: ROUTES.PAGES.TRANSACTIONS },
      { label: translate('notifications'), to: ROUTES.PAGES.NOTIFICATIONS },
      { label: translate('settings'), to: ROUTES.PAGES.SETTINGS.MAIN },
    ],
    [translate],
  )

  const value = useMemo(() => {
    const idx = routes.findIndex((r) =>
      r.to === '/' ? pathname === '/' : pathname.startsWith(r.to),
    )
    return idx === -1 ? false : idx
  }, [pathname, routes])

  const handleOpenMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleCloseMenu = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    if (isLoggingOut) return
    setIsLoggingOut(true)
    try {
      await logoutHelper(dispatch)
    } finally {
      setIsLoggingOut(false)
    }
  }

  return (
    <AppBar position="static" color="transparent" sx={{ bgcolor: 'surface.light' }}>
      <Container maxWidth="xl" sx={{ display: 'flex', alignItems: 'center' }}>
        {!isMobile && (
          <>
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

            <LanguageMenu />

            <ThemeButton />

            <Button
              onClick={handleLogout}
              disabled={isLoggingOut}
              sx={{
                bgcolor: 'transparent',
                '&:hover': { bgcolor: 'transparent' },
                typography: 'caption',
              }}
              endIcon={<LogoutRounded />}
            >
              {translate('logout')}
            </Button>
          </>
        )}

        {isMobile && (
          <>
            <IconButton onClick={handleOpenMenu} sx={{ color: 'gray.main' }}>
              <MenuIcon />
            </IconButton>

            <Menu
              anchorEl={anchorEl}
              open={open}
              onClose={handleCloseMenu}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
            >
              {routes.map((r) => (
                <MenuItem
                  key={r.to}
                  component={RouterLink}
                  to={r.to}
                  onClick={handleCloseMenu}
                  selected={pathname.startsWith(r.to)}
                >
                  {r.label}
                </MenuItem>
              ))}

              <MenuItem
                onClick={() => {
                  handleCloseMenu()
                  handleLogout()
                }}
                disabled={isLoggingOut}
              >
                <TypographyWithAdornment
                  text={translate('logout')}
                  Icon={LogoutRounded}
                  position="end"
                  stackSx={{ justifyContent: 'space-between', width: '100%' }}
                  typographySx={{ color: 'error.main' }}
                  color="error.main"
                />
              </MenuItem>
            </Menu>

            <Box sx={{ flexGrow: 1 }} />

            <ThemeButton />

            <LanguageMenu />
          </>
        )}
      </Container>
    </AppBar>
  )
}
