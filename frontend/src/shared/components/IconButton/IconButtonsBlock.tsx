import { Stack } from '@mui/material'
import { IconButton } from './IconButton'
import { IconButtonItem } from '@shared/types'

type Props = {
  buttons: IconButtonItem[]
}

export const IconButtonsBlock = ({ buttons }: Props) => {
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
      {buttons.map((b, i) => (
        <IconButton key={i} Icon={b.Icon} title={b.title} subtitle={b.subtitle} path={b.path} />
      ))}
    </Stack>
  )
}
