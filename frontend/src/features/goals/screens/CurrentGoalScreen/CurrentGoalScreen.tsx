import { useEffect } from 'react'
import AddIcon from '@mui/icons-material/Add'
import { Button, Paper, Stack, Typography } from '@mui/material'
import { ScreenContent } from '@shared/components'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { useParams } from 'react-router'
import { getGoal, selectCurrentGoal, selectIsCurrentGoalLoading } from '../../store/currentGoal'

export default function GoalScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Goals')
  const params = useParams()
  const goals = useAppSelector(selectCurrentGoal)

  useEffect(() => {
    dispatch(getGoal({ goalId: params.id! }))
  }, [])

  const handleOpenModal = () => dispatch(openModal({ id: MODAL_IDS.CREATE_GOAL }))

  return (
    <ScreenContent title={translate('title')}>
      <Stack spacing={2} sx={{ maxWidth: '800px' }}>
        <Typography>{goals.currentValue}</Typography>
        <Typography>{goals.targetValue}</Typography>
        <Typography>{goals.daysLeft}</Typography>

        <Typography>{goals.finishDate}</Typography>
        <Typography>{goals.goalId}</Typography>
        <Typography>{goals.name}</Typography>
        <Typography>{goals.status}</Typography>

        <Stack>
          {goals.transactions.map((g) => {
            return (
              <Typography key={g.date}>
                {g.date} {g.type} {g.value}
              </Typography>
            )
          })}
        </Stack>
      </Stack>
      <Button onClick={handleOpenModal}>edit</Button>
    </ScreenContent>
  )
}
