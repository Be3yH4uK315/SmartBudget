import { Grid } from '@mui/material'
import { BudgetIcon, SecurityIcon, SupportIcon } from '@shared/assets/icons'
import { NotificationIcon } from '@shared/assets/icons/NotificationIcon'
import { IconButton, ScreenContent } from '@shared/components'
import { ROUTES } from '@shared/constants/routes'
import { useTranslate } from '@shared/hooks'

export default function SettingsScreen() {
  const translate = useTranslate('Settings')

  const buttons = [
    {
      title: translate('Menu.Security.title'),
      subtitle: translate('Menu.Security.subtitle'),
      path: ROUTES.PAGES.SETTINGS.SECURITY,
      Icon: <SecurityIcon />,
    },
    {
      title: translate('Menu.Budget.title'),
      subtitle: translate('Menu.Budget.subtitle'),
      path: ROUTES.PAGES.SETTINGS.BUDGET,
      Icon: <BudgetIcon />,
    },
    {
      title: translate('Menu.Notifications.title'),
      subtitle: translate('Menu.Notifications.subtitle'),
      path: ROUTES.PAGES.SETTINGS.NOTIFICATIONS,
      Icon: <NotificationIcon />,
    },
    {
      title: translate('Menu.Support.title'),
      subtitle: translate('Menu.Support.subtitle'),
      path: ROUTES.PAGES.SETTINGS.SUPPORT,
      Icon: <SupportIcon />,
    },
  ]

  return (
    <ScreenContent title={translate('title')}>
      <Grid container spacing={2} sx={{ maxWidth: '800px' }}>
        {buttons.map((b, i) => (
          <Grid key={i} size={{ xs: 12, md: 6 }}>
            <IconButton
              key={i}
              title={b.title}
              subtitle={b.subtitle}
              path={b.path}
              Icon={b.Icon && b.Icon}
              paperSx={{ display: 'flex', height: '100%' }}
            />
          </Grid>
        ))}
      </Grid>
    </ScreenContent>
  )
}
