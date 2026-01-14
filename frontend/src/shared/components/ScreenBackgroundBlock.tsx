import { Box, SxProps } from '@mui/material'

type Props = {
  boxSx?: SxProps
}

export const ScreenBackgroundBlock = ({ boxSx }: Props) => {
  return (
    <Box
      sx={{
        ...boxSx,
        position: 'absolute',
        top: 32,
        left: -50,
        right: -50,
        height: 400,
        borderRadius: '32px',
        zIndex: 10,
        background: (theme) =>
          `linear-gradient(
                180deg,
                ${theme.palette.primary.main} 0%,
                ${theme.palette.primary.main} 30%,
                transparent 100%
              )`,
      }}
    />
  )
}
