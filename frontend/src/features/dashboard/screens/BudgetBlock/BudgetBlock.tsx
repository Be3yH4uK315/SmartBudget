import React from 'react'
import { Button, Paper, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { useNavigate } from 'react-router'
import { PercentLine } from './PercentLine'
import { DashboardCategory } from '@features/dashboard/types'

type Props = {
  categories: DashboardCategory[]
  budgetLimit: number
}

export const BudgetBlock = React.memo(({ categories, budgetLimit }: Props) => {
  const translate = useTranslate('Dashboard.Budget')
  const navigate = useNavigate()

  const title = categories.length > 0 ? translate('title') : translate('emptyTitle')

  return (
    <Paper
      sx={{
        p: 3,
        borderRadius: '24px',
        maxWidth: { xs: 'auto', md: '400px' },
        minWidth: '300px',
      }}
    >
      <Stack spacing={1}>
        <Typography variant="h4">{title}</Typography>

        {categories.length > 0 && <PercentLine categories={categories} limit={budgetLimit} />}

        {!categories.length && (
          <Button
            variant="gray"
            sx={{ height: 'auto', width: '100%' }}
            onClick={() => navigate('/budget')}
          >
            {translate('createButton')}
          </Button>
        )}
      </Stack>
    </Paper>
  )
})
