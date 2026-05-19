import { goalsApi } from '@features/goals/api'
import { GoalSearchItem, GoalsStats } from '@features/goals/components'
import { useGoalsFilters } from '@features/goals/hooks'
import { selectGoals, selectGoalsStats, selectIsGoalsLoading } from '@features/goals/store/goals'
import { GoalSearchOption } from '@features/goals/types'
import { Add, ArchiveOutlined } from '@mui/icons-material'
import { Button, Stack } from '@mui/material'
import { EmptyList, ScreenContent, SearchBar } from '@shared/components'
import { MODAL_IDS, ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { useNavigate } from 'react-router'
import { GoalBlock } from './GoalBlock'
import { GoalsFiltersBlock } from './GoalsFiltersBlock'
import { GoalsScreenSkeleton } from './GoalsScreenSkeleton'

export default function GoalsScreen() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const translate = useTranslate('Goals')

  const isLoading = useAppSelector(selectIsGoalsLoading)
  const goals = useAppSelector(selectGoals)
  const goalsStats = useAppSelector(selectGoalsStats)
  const { isDirty, ...props } = useGoalsFilters()

  const handleOpenModal = () => dispatch(openModal({ id: MODAL_IDS.CREATE_GOAL }))

  const translationKey =
    props.localFilters.tags.length > 0
      ? props.localFilters.isArchived
        ? 'NoGoals.Filtered.Archive'
        : 'NoGoals.Filtered'
      : props.localFilters.isArchived
        ? 'NoGoals.Empty.Archive'
        : 'NoGoals.Empty'

  const emptyListReason = {
    title: translate(`${translationKey}.title`),
    subtitle: translate(`${translationKey}.subtitle`),
  }

  return (
    <ScreenContent
      isLoading={isLoading}
      isBackButton={props.appliedFiltersRef.current.isArchived}
      title={
        !props.appliedFiltersRef.current.isArchived ? translate('title') : translate('archiveTitle')
      }
      ContentSkeleton={GoalsScreenSkeleton}
    >
      <Stack spacing={2} sx={{ maxWidth: '800px' }}>
        <SearchBar<GoalSearchOption>
          apiFunc={goalsApi.searchGoals}
          getOptionLabel={(option) => option.name}
          renderOption={(props, option) => (
            <GoalSearchItem {...props} key={option.goalId} goal={option} />
          )}
        />

        {goals.length === 0 && (
          <EmptyList
            reasonTitle={emptyListReason.title}
            reasonSubtitle={emptyListReason.subtitle}
          />
        )}

        {goals.length === 0 &&
          (props.localFilters.tags.length > 0 || props.localFilters.priority.length > 0) && (
            <Button
              onClick={props.handleClearFilters}
              sx={{ height: 'min-content' }}
              variant="yellow"
            >
              {translate('Tags.clear')}
            </Button>
          )}

        {goals.length > 0 && <GoalsStats {...goalsStats} />}

        {!props.appliedFiltersRef.current.isArchived && (
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

        {goals.length > 0 && <GoalsFiltersBlock isDirty={isDirty()} {...props} />}

        {goals.length > 0 && goals.map((g) => <GoalBlock key={g.goalId} goal={g} />)}
      </Stack>
    </ScreenContent>
  )
}
