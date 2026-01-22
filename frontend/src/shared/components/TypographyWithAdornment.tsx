import { ComponentType } from 'react'
import { Stack, SvgIconProps, SxProps, Typography } from '@mui/material'

type Props = {
  Icon: ComponentType<SvgIconProps>
  iconSize?: 'small' | 'large' | 'medium'
  text: string
  stackSx?: SxProps
  typographySx?: SxProps
  typographyVariant?: 'h4' | 'body1' | 'caption'
  color?: string
  position?: 'start' | 'end'
}

export const TypographyWithAdornment = ({
  Icon,
  iconSize = 'small',
  text,
  stackSx,
  typographySx,
  typographyVariant = 'body1',
  color = 'text.primary',
  position = 'start',
}: Props) => {
  return (
    <Stack
      direction={'row'}
      spacing={0.5}
      sx={{ alignItems: 'center', height: '100%', ...stackSx }}
    >
      {position === 'start' && <Icon fontSize={iconSize} sx={{ color }} />}

      <Typography variant={typographyVariant} sx={{ color, ...typographySx }}>
        {text}
      </Typography>

      {position === 'end' && <Icon fontSize="small" sx={{ color }} />}
    </Stack>
  )
}
