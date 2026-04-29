import { Box, Paper, Stack, Typography } from '@mui/material'
import { IconButtonItem } from '@shared/types'
import { noop } from '@shared/utils/noop'
import { Link } from 'react-router'

export const IconButton = ({ title, subtitle, Icon, path, paperSx, onClick }: IconButtonItem) => {
  const content = (
    <Stack spacing={2} direction={'row'} sx={{ alignItems: 'center', whiteSpace: 'wrap' }}>
      {Icon && (
        <Box
          sx={{
            bgcolor: 'secondary.main',
            width: 'max-content',
            height: 'max-content',
            borderRadius: '24px',
            p: 1,
            lineHeight: 0,
            color: '#FFFFFF',
          }}
        >
          {Icon}
        </Box>
      )}

      <Stack spacing={0.5}>
        {title && <Typography variant="h4">{title}</Typography>}

        {subtitle && <Typography>{subtitle}</Typography>}
      </Stack>
    </Stack>
  )

  return (
    <Paper
      role="button"
      sx={{
        p: 3,
        borderRadius: '24px',
        flex: '1 1 0%',
        textDecoration: 'none',
        cursor: 'pointer',
        ...paperSx,
      }}
      component={path ? Link : 'div'}
      to={path && path}
      elevation={2}
      onClick={onClick ? onClick : noop}
    >
      {content}
    </Paper>
  )
}
