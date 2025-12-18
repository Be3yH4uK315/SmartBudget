import { useEffect } from 'react'
import { GoalsStats } from '@features/goals/components'
import {
  clearGoalsState,
  getGoals,
  selectGoals,
  selectGoalsStats,
  selectIsGoalsLoading,
} from '@features/goals/store/goals'
import AddIcon from '@mui/icons-material/Add'
import { Button, Paper, Stack, Typography } from '@mui/material'
import { ScreenContent } from '@shared/components'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { GoalBlock } from './GoalBlock'
import { GoalsScreenSkeleton } from './GoalsScreenSkeleton'

export default function GoalsScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Goals')
  const isLoading = useAppSelector(selectIsGoalsLoading)
  const goals = useAppSelector(selectGoals)
  const goalsStats = useAppSelector(selectGoalsStats)

  useEffect(() => {
    dispatch(getGoals())
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    return () => {
      dispatch(clearGoalsState())
    }
  }, [dispatch])

  const handleOpenModal = () => dispatch(openModal({ id: MODAL_IDS.CREATE_GOAL }))

  return (
    <ScreenContent
      isLoading={isLoading}
      title={translate('title')}
      ContentSkeleton={GoalsScreenSkeleton}
    >
      <Stack spacing={2} sx={{ maxWidth: '800px' }}>
        {goals.length === 0 && (
          <>
            <Paper
              sx={{
                pt: 1,
                bgcolor: 'transparent',
                minHeight: '150px',
                borderRadius: '32px',
                textAlign: 'center',
              }}
            >
              <Stack
                spacing={1}
                sx={{
                  height: '100%',
                  borderStyle: 'dashed',
                  borderColor: 'gray.main',
                  borderWidth: '2px',
                  justifyContent: 'center',
                  borderRadius: '24px',
                  color: 'gray.main',
                  p: 1,
                }}
              >
                <Typography variant="h3" sx={{ color: 'gray.main' }}>
                  {translate('noGoals.title')}
                </Typography>

                <Typography variant="caption" sx={{ color: 'gray.main' }}>
                  {translate('noGoals.subtitle')}
                </Typography>
              </Stack>
            </Paper>
            <Button startIcon={<AddIcon />} onClick={handleOpenModal}>
              {translate('create')}
            </Button>
          </>
        )}

        {goals.length > 0 && (
          <Stack spacing={2}>
            <GoalsStats
              targetValue={goalsStats.targetValue}
              currentValue={goalsStats.currentValue}
            />

            <Button startIcon={<AddIcon />} onClick={handleOpenModal}>
              {translate('create')}
            </Button>

            {goals.map((g) => (
              <GoalBlock key={g.goalId} goal={g} />
            ))}
          </Stack>
        )}
      </Stack>
    </ScreenContent>
  )
}
