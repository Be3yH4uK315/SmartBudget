import { Button, Paper, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { useNavigate } from 'react-router'
import { Goal } from '../../types'

type Props = {
  goal: Goal
}

export const GoalBlock = ({ goal }: Props) => {
  const translate = useTranslate('')
  const navigate = useNavigate()

  return (
    <Paper component={Button} onClick={() => navigate(`./${goal.goalId}`)}>
      <Stack spacing={2}>
        <Typography variant="h5">{goal.name}</Typography>

        <Stack>
          <Typography>
            {translate('currentValue')}
            {goal.currentValue}
          </Typography>

          <Typography>
            {translate('achieveValue')}
            {goal.targetValue - goal.currentValue}
          </Typography>

          <Typography>
            {translate('finishDate')}
            {goal.finishDate}
          </Typography>
        </Stack>
      </Stack>
    </Paper>
  )
}
