import { DashboardGoal } from '@features/dashboard/types'
import { Button, Stack, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { useNavigate } from 'react-router'
import { Goal } from './Goal'

type Props = {
  goals: DashboardGoal[]
}

export const GoalsBlock = ({ goals }: Props) => {
  const translate = useTranslate('Dashboard.Goal')
  const navigate = useNavigate()

  const title = goals.length > 0 ? translate('title') : translate('emptyTitle')

  return (
    <StyledPaper
      paperSx={{
        p: 3,
        maxWidth: { xs: 'auto', md: '400px' },
        minWidth: '300px',
      }}
    >
      <Typography variant="h4">{title}</Typography>

      <Stack spacing={2}>
        <Stack>
          {goals.map((g, i) => (
            <Goal key={i} title={g.name} totalValue={g.totalValue} currentValue={g.currentValue} />
          ))}
        </Stack>

        <Button
          variant="gray"
          sx={{ height: 'auto', width: '100%' }}
          onClick={() => navigate(ROUTES.PAGES.GOALS.MAIN)}
        >
          {translate('createButton')}
        </Button>
      </Stack>
    </StyledPaper>
  )
}
