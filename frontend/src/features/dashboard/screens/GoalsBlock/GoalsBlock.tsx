import { Button, Paper, Stack, Typography } from '@mui/material'
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
        <Stack>
          {goals.map((g, i) => (
            <Goal key={i} title={g.name} totalValue={g.totalValue} currentValue={g.currentValue} />
          ))}
        </Stack>

        <Button
          variant="gray"
          sx={{ height: 'auto', width: '100%' }}
          onClick={() => navigate('/goals')}
        >
          {translate('createButton')}
        </Button>
      </Stack>
    </Paper>
  )
}
