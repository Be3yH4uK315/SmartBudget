import { AppBar, Box, Button, Container, Typography } from '@mui/material'
import { ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { Link as RouterLink } from 'react-router'
import { LanguageMenu } from './LanguageMenu'
import { ThemeButton } from './ThemeButton'

export const PublicHeader = () => {
  const translate = useTranslate('PublicPage')

  return (
    <AppBar position="static" color="transparent" sx={{ bgcolor: 'surface.light' }}>
      <Container maxWidth="xl" sx={{ display: 'flex', alignItems: 'center', py: 0.5 }}>
        <Typography variant="h6" sx={{ letterSpacing: '-0.5px' }}>
          {translate('headerTitle')}
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        <ThemeButton />
        <LanguageMenu />

        <Button
          component={RouterLink}
          to={ROUTES.PAGES.LOGIN}
          variant="yellow"
          size="small"
          sx={{ ml: 1, typography: 'caption', height: 'max-content', textAlign: 'center' }}
        >
          {translate('loginButton')}
        </Button>
      </Container>
    </AppBar>
  )
}
