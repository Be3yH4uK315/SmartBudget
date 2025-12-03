import { Button, Paper, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { useNavigate } from 'react-router'
import { BudgetProgress } from './PercentLine'

type Props = {
  categories: DashboardCategory[]
  budgetLimit: number
}

export const BudgetBlock = ({ categories, budgetLimit }: Props) => {
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
        flex: '1 1 0%',
      }}
    >
      <Typography variant="h4">{title}</Typography>

      <Stack spacing={2}>
        {categories.length && <BudgetProgress categories={categories} limit={budgetLimit} />}

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
}
