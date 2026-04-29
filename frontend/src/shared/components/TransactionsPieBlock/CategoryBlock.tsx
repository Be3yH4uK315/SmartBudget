import React from 'react'
import { Box, Stack, Typography } from '@mui/material'
import { PieDataItem } from '@shared/types/components'
import { formatCurrency } from '@shared/utils'

type Props = {
  category: PieDataItem
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
