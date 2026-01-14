import React from 'react'
import { INCOME_CATEGORY_ID } from '@features/budget/constants/incomeCategory'
import { DashboardCategory } from '@features/dashboard/types'
import { Button, Paper, Stack, Typography } from '@mui/material'
import { PercentLine } from '@shared/components'
import { ROUTES } from '@shared/constants/routes'
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
  const currentValue = categories.reduce((sum, c) => {
    if (c.value > 0 && c.categoryId !== INCOME_CATEGORY_ID) return sum + c.value
    return sum
  }, 0)

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

        {categories.length > 0 && budgetLimit !== 0 && (
          <PercentLine currentValue={currentValue} limit={budgetLimit} />
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
    </Paper>
  )
})
