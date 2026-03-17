import React from 'react'
import { DashboardCategory } from '@features/dashboard/types'
import { calcBudgetStats } from '@features/dashboard/utils'
import { Button, Stack, Typography } from '@mui/material'
import { PercentLine, StyledPaper } from '@shared/components'
import { ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { useNavigate } from 'react-router'

type Props = {
  categories: DashboardCategory[]
  budgetLimit: number
}

export const BudgetBlock = React.memo(({ categories, budgetLimit }: Props) => {
  const translate = useTranslate('Dashboard.Budget')
  const navigate = useNavigate()

  const title = categories.length > 0 ? translate('title') : translate('emptyTitle')

  if (!categories.length && budgetLimit === 0) return null

  return (
    <StyledPaper
      paperSx={{
        p: 3,
        maxWidth: { xs: 'auto', md: '400px' },
        minWidth: '300px',
      }}
    >
      <Stack spacing={1}>
        <Typography variant="h4">{title}</Typography>

        {categories.length > 0 && (
          <PercentLine currentValue={calcBudgetStats(categories)} limit={budgetLimit} />
        )}

        {!categories.length && (
          <Button
            variant="gray"
            sx={{ height: 'auto', width: '100%' }}
            onClick={() => navigate(ROUTES.PAGES.BUDGET)}
          >
            {translate('createButton')}
          </Button>
        )}
      </Stack>
    </StyledPaper>
  )
})
