import { useEffect } from 'react'
import { GoalsStats } from '@features/goals/components'
import {
  clearGoalsState,
  getGoals,
  resetFilters,
  selectGoals,
  selectGoalsFilters,
  selectGoalsStats,
  selectIsGoalsLoading,
  setIsArchived,
} from '@features/goals/store/goals'
import { Add, ArchiveOutlined } from '@mui/icons-material'
import { Button, Stack } from '@mui/material'
import { ScreenContent } from '@shared/components'
import { MODAL_IDS, ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { useMatch, useNavigate } from 'react-router'
import { EmptyGoalsList } from './EmptyGoalsList'
import { GoalBlock } from './GoalBlock'
import { GoalsFiltersBlock } from './GoalsFiltersBlock'
import { GoalsScreenSkeleton } from './GoalsScreenSkeleton'

export default function GoalsScreen() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const translate = useTranslate('Goals')

  const isArchivePage = !!useMatch(ROUTES.PAGES.GOALS.ARCHIVE)

  const isLoading = useAppSelector(selectIsGoalsLoading)
  const goals = useAppSelector(selectGoals)
  const goalsStats = useAppSelector(selectGoalsStats)
  const filters = useAppSelector(selectGoalsFilters)

  const handleOpenModal = () => dispatch(openModal({ id: MODAL_IDS.CREATE_GOAL }))

  const handleClearFilters = () => {
    dispatch(resetFilters())
    dispatch(getGoals())
  }

  useEffect(() => {
    dispatch(setIsArchived(isArchivePage))
    dispatch(getGoals())

    return () => {
      dispatch(clearGoalsState())
    }
  }, [dispatch, isArchivePage])

  return (
    <ScreenContent
      isLoading={isLoading}
      isBackButton={isArchivePage}
      title={!isArchivePage ? translate('title') : translate('archiveTitle')}
      ContentSkeleton={GoalsScreenSkeleton}
    >
      <Stack spacing={2} sx={{ maxWidth: '800px' }}>
        {goals.length === 0 && (
          <EmptyGoalsList filtersLength={filters.tags.length} isArchive={isArchivePage} />
        )}

        {goals.length === 0 && filters.tags.length > 0 && (
          <Button onClick={handleClearFilters} sx={{ height: 'min-content' }} variant="yellow">
            {translate('Tags.clear')}
          </Button>
        )}

        {goals.length > 0 && <GoalsStats {...goalsStats} />}

        {!isArchivePage && (
          <Stack direction={'row'} spacing={2} alignItems={'stretch'}>
            <Button
              startIcon={<Add />}
              onClick={handleOpenModal}
              sx={{ height: 'min-content' }}
              variant="yellow"
              fullWidth
            >
              {translate('create')}
            </Button>

            <Button
              startIcon={<ArchiveOutlined />}
              onClick={() => navigate(ROUTES.PAGES.GOALS.ARCHIVE)}
              sx={{ height: 'auto', width: 'max-content' }}
              variant="yellow"
            >
              {translate('Tags.archive')}
            </Button>
          </Stack>
        )}

        {goals.length > 0 && <GoalsFiltersBlock filters={filters} />}

        {goals.length > 0 && goals.map((g) => <GoalBlock key={g.goalId} goal={g} />)}
      </Stack>
    </ScreenContent>
  )
}
