import { useEffect } from 'react'
import { GoalsStats } from '@features/goals/components'
import {
  clearCurrentGoalState,
  getGoal,
  selectCurrentGoal,
  selectIsCurrentGoalLoading,
} from '@features/goals/store/currentGoal'
import { ArrowBackOutlined } from '@mui/icons-material'
import { Box, Button, IconButton as MUIIconButton, Paper, Stack, Typography } from '@mui/material'
import { IconButton, ScreenContent, TransactionsPieBlock } from '@shared/components'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTransactionFilters, useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { CenterLabel } from '@shared/types/components'
import { formatPercent } from '@shared/utils/formatPercent'
import { mapGoalTransaction } from '@shared/utils/transactionsBlockAdapters'
import dayjs from 'dayjs'
import { useNavigate, useParams } from 'react-router'

export default function GoalScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('CurrentGoal')
  const navigate = useNavigate()
  const params = useParams()

  const goal = useAppSelector(selectCurrentGoal)
  const isLoading = useAppSelector(selectIsCurrentGoalLoading)

  const { activeType, toggleFilter, normalizedData } = useTransactionFilters(
    goal.transactions,
    mapGoalTransaction,
    'income',
  )

  const transactionsBlockTitle = translate('TransactionsPieBlock.title')

  const centerLabel: CenterLabel = {
    type: 'amount',
    total: goal.currentValue,
    label: translate(`TransactionsPieBlock.${activeType}`).toLowerCase(),
  }

  const settingsButtonTitle = translate('settings')
  const settingsButtonSubtitle = translate('settingsSubtitle')

  const handleClose = () => {
    dispatch(clearCurrentGoalState())
    navigate(-1)
  }

  const handleOpenModal = () =>
    dispatch(openModal({ id: MODAL_IDS.CREATE_GOAL, props: { goal: goal } }))

  useEffect(() => {
    if (params.id) dispatch(getGoal({ goalId: params.id }))
    return
  }, [params.id, dispatch])

  useEffect(() => {
    return () => {
      dispatch(clearCurrentGoalState())
    }
  }, [dispatch])

  return (
    <ScreenContent isLoading={isLoading}>
      <Box
        sx={{
          position: 'absolute',
          top: 32,
          left: -50,
          right: -50,
          height: 400,
          borderRadius: '32px',
          zIndex: 10,
          background: (theme) =>
            `linear-gradient(
                180deg,
                ${theme.palette.primary.main} 0%,
                ${theme.palette.primary.main} 30%,
                transparent 100%
              )`,
        }}
      />

      <Stack spacing={2} sx={{ zIndex: 20, pt: 4 }}>
        <MUIIconButton
          onClick={handleClose}
          sx={{ display: 'flex', justifyContent: 'flex-start', width: 'max-content' }}
        >
          <ArrowBackOutlined />

          <Typography>{translate('goBack')}</Typography>
        </MUIIconButton>
        <Typography variant="h3" pl={2}>
          {goal.name}
        </Typography>

        <Typography pl={2}>
          {translate('finishDate', { date: dayjs(goal.finishDate).format('DD.MM.YYYY') })}
        </Typography>

        <Stack direction={{ md: 'row' }} spacing={{ xs: 2, md: 2 }} width={'100%'}>
          <Stack spacing={2} width={{ xs: '100%', md: '50%' }}>
            <Paper
              elevation={2}
              sx={{
                px: 3,
                py: 2,
                height: 'max-content',
                borderRadius: '24px',
                display: 'flex',
                flexDirection: 'column',
                mx: 0,
              }}
            >
              <Typography variant="h4">
                {formatPercent(goal.currentValue / goal.targetValue)}
              </Typography>

              <Typography>{translate('progress')}</Typography>

              <Typography variant="caption">{translate('autoAdd')}</Typography>
            </Paper>
          </Stack>

          <Stack spacing={2}>
            <TransactionsPieBlock
              title={transactionsBlockTitle}
              activeType={activeType}
              pieData={normalizedData}
              centerLabel={centerLabel}
              toggleFilter={toggleFilter}
            />

            <GoalsStats
              targetValue={goal.targetValue}
              currentValue={goal.currentValue}
              daysLeft={goal.daysLeft}
            />

            <IconButton
              onClick={handleOpenModal}
              title={settingsButtonTitle}
              subtitle={settingsButtonSubtitle}
            />

            <Button sx={{ color: 'error.main' }}>{translate('closeGoal')}</Button>
          </Stack>
        </Stack>
      </Stack>
    </ScreenContent>
  )
}
