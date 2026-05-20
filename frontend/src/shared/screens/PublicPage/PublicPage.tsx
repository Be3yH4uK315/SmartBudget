import {
  AccountBalanceWalletRounded,
  AutoAwesomeRounded,
  FlagRounded,
  NotificationsActiveRounded,
} from '@mui/icons-material'
import { Box, Button, Container, Grid, Stack, Typography } from '@mui/material'
import { ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { selectUser, useAppSelector } from '@shared/store'
import { FeatureCard as FeatureCardType } from '@shared/types/components'
import { Link as RouterLink, Navigate } from 'react-router'
import { FeatureCard } from './FeatureCard'
import { StepBlock } from './StepBlock'

export const PublicPage = () => {
  const { isAuth } = useAppSelector(selectUser)
  const translate = useTranslate('PublicPage')

  const features: FeatureCardType[] = [
    {
      Icon: AccountBalanceWalletRounded,
      title: 'Feature.One.title',
      subtitle: 'Feature.One.subtitle',
    },
    {
      Icon: AutoAwesomeRounded,
      title: 'Feature.Two.title',
      subtitle: 'Feature.Two.subtitle',
    },
    {
      Icon: FlagRounded,
      title: 'Feature.Three.title',
      subtitle: 'Feature.Three.subtitle',
    },
    {
      Icon: NotificationsActiveRounded,
      title: 'Feature.Four.title',
      subtitle: 'Feature.Four.subtitle',
    },
  ]

  if (isAuth) {
    return <Navigate to={ROUTES.PAGES.DASHBOARD} replace />
  }

  return (
    <Box sx={{ width: '100%', overflowX: 'hidden' }}>
      <Box
        sx={{
          background: (theme) =>
            `linear-gradient(
                180deg,
                ${theme.palette.primary.main} 0%,
                ${theme.palette.primary.main} 30%,
                transparent 100%
              )`,
          py: { xs: 8, md: 12 },
        }}
      >
        <Container maxWidth="md">
          <Stack alignItems="center" spacing={5}>
            <Stack alignItems="center" textAlign="center" spacing={3}>
              <Typography
                variant="h2"
                sx={{
                  color: 'gray.dark',
                }}
              >
                {translate('heroTitle')}
              </Typography>

              <Typography sx={{ color: 'gray.dark', maxWidth: 560 }}>
                {translate('heroSubtitle')}
              </Typography>
            </Stack>

            <Button
              component={RouterLink}
              to={ROUTES.PAGES.LOGIN}
              sx={{
                bgcolor: 'gray.dark',
                color: '#fff',
                px: 5,
                py: 1.5,
                '&:hover': { bgcolor: 'gray.dark', opacity: 0.85 },
              }}
            >
              {translate('heroCta')}
            </Button>
          </Stack>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 10 } }}>
        <Typography variant="h3" textAlign="center" gutterBottom sx={{ mb: 5 }}>
          {translate('featuresTitle')}
        </Typography>

        <Grid container spacing={3}>
          {features.map(({ Icon, title, subtitle }) => (
            <Grid key={title} size={{ xs: 12, sm: 6, md: 3 }}>
              <FeatureCard Icon={Icon} title={translate(title)} subtitle={translate(subtitle)} />
            </Grid>
          ))}
        </Grid>
      </Container>

      <Box sx={{ bgcolor: 'surface.light', py: { xs: 6, md: 10 } }}>
        <Container maxWidth="sm">
          <Typography variant="h3" textAlign="center" sx={{ mb: 5 }}>
            {translate('howItWorks')}
          </Typography>

          <StepBlock />
        </Container>
      </Box>

      <Box sx={{ bgcolor: 'surface.main', py: { xs: 6, md: 10 } }}>
        <Container maxWidth="sm">
          <Stack alignItems="center" textAlign="center" spacing={3}>
            <Typography variant="h4">{translate('ctaTitle')}</Typography>

            <Button
              component={RouterLink}
              to={ROUTES.PAGES.LOGIN}
              variant="yellow"
              sx={{ px: 5, py: 1.5 }}
            >
              {translate('ctaButton')}
            </Button>
          </Stack>
        </Container>
      </Box>
    </Box>
  )
}
