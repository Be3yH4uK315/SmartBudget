import { Grid } from '@mui/material'
import { IconButton, ScreenContent } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'

export default function SettingsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings')

  const buttons = [
    {
      title: 'Безопасность',
      subtitle: 'Смена пароля и активные сессии',
      path: '',
    },
    {
      title: 'Уведомления',
      subtitle: '',
      path: '',
    },
    {
      title: 'as',
      subtitle: '',
      path: '',
    },
    {
      title: 'as',
      subtitle: '',
      path: '',
    },
  ]

  return (
    <ScreenContent>
      <Grid container spacing={2}>
        {buttons.map((b, i) => (
          <Grid key={i} size={{ xs: 12, md: 6 }}>
            <IconButton key={i} title={b.title} subtitle={b.subtitle} path={b.path} />
          </Grid>
        ))}
      </Grid>
    </ScreenContent>
  )
}
