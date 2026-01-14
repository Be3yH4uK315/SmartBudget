import { Stack, SvgIconTypeMap, Typography } from '@mui/material'
import { OverridableComponent } from '@mui/material/OverridableComponent'
import { useTranslate } from '@shared/hooks'

type Props = {
  value: number
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  Icon?: OverridableComponent<SvgIconTypeMap<{}, 'svg'>>
}

export const CategoryOption = ({ value, Icon }: Props) => {
  const translate = useTranslate('Categories')

  return (
    <Stack direction="row" spacing={1} alignItems="center">
      {Icon && <Icon fontSize="small" />}

      <Typography>{translate(value)}</Typography>
    </Stack>
  )
}
