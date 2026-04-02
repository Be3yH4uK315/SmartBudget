import { ServiceBlock as ServiceBlockType } from '@features/settings/types'
import { Stack, Switch, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'

type Props = ServiceBlockType & {
  subtitle?: string
}

export const ServiceBlock = ({ title, subtitle, options }: Props) => {
  const translate = useTranslate('Settings.Notifications')

  return (
    <StyledPaper noElevation>
      <Stack>
        <Stack>
          <Typography variant="h4">{translate(title)}</Typography>

          {subtitle && <Typography>{translate(subtitle)}</Typography>}
        </Stack>

        <Stack>
          {options.map((o) => (
            <Stack
              key={o.title}
              spacing={2}
              direction={'row'}
              sx={{ justifyContent: 'space-between', display: 'flex', alignItems: 'center' }}
            >
              <Typography>{translate(o.title)}</Typography>

              <Switch checked={o.isChecked} onClick={o.onClick} />
            </Stack>
          ))}
        </Stack>
      </Stack>
    </StyledPaper>
  )
}
