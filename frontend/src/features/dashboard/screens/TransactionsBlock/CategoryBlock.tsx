import React from 'react'
import { formatCurrency } from '@features/dashboard/utils'
import { Box, Stack, Typography } from '@mui/material'

type Props = {
  category: normalizedCategory
}

export const CategoryBlock = React.memo(({ category }: Props) => {
  return (
    <Box
      component="span"
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        backgroundColor: category.lightColor,
        px: 1.5,
        py: 0.5,
        borderRadius: '6px',
      }}
    >
      <Stack direction={'row'} spacing={1.5} alignItems={'center'}>
        <Box sx={{ width: 12, height: 12, borderRadius: '6px', backgroundColor: category.color }} />

        <Typography variant="caption" noWrap>
          {category.label} {formatCurrency(category.value)}
        </Typography>
      </Stack>
    </Box>
  )
})
