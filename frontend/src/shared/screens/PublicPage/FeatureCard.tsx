import { Box, Typography } from '@mui/material'
import type { FeatureCard as Props } from '@shared/types/components'

export const FeatureCard = ({ Icon, title, subtitle }: Props) => (
  <Box
    sx={{
      bgcolor: 'surface.light',
      borderRadius: 3,
      p: 3,
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      gap: 1.5,
    }}
  >
    <Box
      sx={{
        width: 48,
        height: 48,
        borderRadius: 2,
        bgcolor: 'secondary.main',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      <Icon sx={{ color: '#fff', fontSize: 26 }} />
    </Box>

    <Typography variant="h6">{title}</Typography>

    <Typography>{subtitle}</Typography>
  </Box>
)
