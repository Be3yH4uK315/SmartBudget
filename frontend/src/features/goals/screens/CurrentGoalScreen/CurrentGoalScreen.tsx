import { useEffect } from 'react'
import { GoalsStats } from '@features/goals/components'
import { CurrentGoalTagsBlock } from '@features/goals/components/GoalTags'
import {
  clearCurrentGoalState,
  getGoal,
  getGoalTransactions,
  selectCurrentGoal,
  selectGoalTransactions,
  selectIsCurrentGoalLoading,
  updateArchivedStatus,
  updateGoalStatus,
} from '@features/goals/store/currentGoal'
import { ArrowBackOutlined } from '@mui/icons-material'
import { IconButton as MUIIconButton, Stack, Typography, useTheme } from '@mui/material'
import {
  IconButton,
  ScreenBackgroundBlock,
  ScreenContent,
  TransactionsPieBlock,
} from '@shared/components'
import { MODAL_IDS, ROUTES } from '@shared/constants'
import { useTransactionFilters, useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { CenterLabel, PieDataItem } from '@shared/types/components'
import { mapGoalTransaction } from '@shared/utils'
import { useNavigate, useParams } from 'react-router'
import { ActionsButtonsBlock } from './ActionsButtonsBlock'
import { CurrentGoalScreenSkeleton } from './CurrentGoalScreenSkeleton'
import { GoalInfoBlock } from './GoalInfo'
import { ProgressBlock } from './ProgressBlock'

export default function GoalScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('CurrentGoal')
  const navigate = useNavigate()
  const params = useParams()
  const theme = useTheme()

  const goal = useAppSelector(selectCurrentGoal)
  const isLoading = useAppSelector(selectIsCurrentGoalLoading)
  const transactions = useAppSelector(selectGoalTransactions)

  const {
    goalId,
    name,
    currentAmount,
    finishDate,
    status,
    targetAmount,
    tags,
    priority,
    recommendedPayment,
    daysLeft,
    isArchived,
  } = goal

  const { activeType, toggleFilter, normalizedData } = useTransactionFilters(
    transactions,
    mapGoalTransaction,
    'income',
  )

  const centerLabel: CenterLabel = {
    type: 'amount',
    total: currentAmount,
    label: translate(`TransactionsPieBlock.${activeType}`).toLowerCase(),
  }

  const remainingValue: PieDataItem = {
    value: targetAmount - currentAmount,
    color: theme.palette.grayButton.dark,
  }

  const handleOpenModal = () =>
    dispatch(openModal({ id: MODAL_IDS.CREATE_GOAL, props: { goal: goal } }))

  const handleStatusChange = () => dispatch(updateGoalStatus({ goalId, status }))
  const handleArchivedChange = () => dispatch(updateArchivedStatus(goalId))

  useEffect(() => {
    const loadGoal = async (id: string) => {
      try {
        await dispatch(getGoal({ goalId: id })).unwrap()
        dispatch(getGoalTransactions({ goalId: id }))
      } catch {
        navigate(ROUTES.GO_BACK)
      }
    }

    if (params.id) loadGoal(params.id)

    return () => {
      dispatch(clearCurrentGoalState())
    }
  }, [params.id, dispatch, navigate])

  return (
    <ScreenContent isLoading={isLoading} ContentSkeleton={CurrentGoalScreenSkeleton}>
      <ScreenBackgroundBlock />

      <Stack spacing={2} sx={{ zIndex: 20, pt: 4 }}>
        <MUIIconButton
          onClick={() => navigate(-1)}
          sx={{
            display: 'flex',
            justifyContent: 'flex-start',
            width: 'max-content',
            borderRadius: '6px',
          }}
        >
          <ArrowBackOutlined />

          <Typography color="#333">{translate('goBack')}</Typography>
        </MUIIconButton>

        <Stack direction={{ md: 'row' }} spacing={{ xs: 2, md: 2 }} width={'100%'}>
          <Stack spacing={2} width={{ xs: '100%', md: '35%' }}>
            <GoalInfoBlock
              name={name}
              status={status}
              finishDate={finishDate}
              isArchived={isArchived}
              targetAmount={targetAmount}
              currentAmount={currentAmount}
            />

            <ProgressBlock currentAmount={currentAmount} targetAmount={targetAmount} />

            <CurrentGoalTagsBlock tags={tags} priority={priority} onClick={handleOpenModal} />
          </Stack>

          <Stack spacing={2} maxWidth={{ xs: '100%', md: '65%' }}>
            <TransactionsPieBlock
              title={translate('TransactionsPieBlock.title')}
              activeType={activeType}
              pieData={normalizedData}
              centerLabel={centerLabel}
              toggleFilter={toggleFilter}
              remainingValue={remainingValue}
            />

            {finishDate && (
              <GoalsStats
                targetAmount={targetAmount}
                currentAmount={currentAmount}
                recommendedPayment={recommendedPayment}
                daysLeft={daysLeft}
              />
            )}

            <IconButton
              onClick={handleOpenModal}
              title={translate('Settings.title')}
              subtitle={translate('Settings.subtitle')}
            />

            <ActionsButtonsBlock
              status={status}
              isArchived={isArchived}
              onStatusClick={handleStatusChange}
              onArchivedClick={handleArchivedChange}
            />
          </Stack>
        </Stack>
      </Stack>
    </ScreenContent>
  )
}
