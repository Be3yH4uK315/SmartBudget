import { useEffect, useMemo } from 'react'
import { useTransactionFilters } from '@features/dashboard/hooks'
import {
  getDashboardData,
  selectBudgetLimit,
  selectCategories,
  selectGoals,
  selectIsDashboardLoading,
} from '@features/dashboard/store'
import { Stack } from '@mui/material'
import { BudgetIcon, GoalIcon, ProfileIcon, SecurityIcon } from '@shared/assets/icons'
import { withAuth } from '@shared/components/hocs'
import { IconButtonsBlock } from '@shared/components/IconButton/IconButtonsBlock'
import { ScreenContent } from '@shared/components/ScreenContent'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { selectUser } from '@shared/store/user'
import { BudgetBlock } from './BudgetBlock'
import { DashboardScreenSkeleton } from './DashboardScreenSkeleton'
import { GoalsBlock } from './GoalsBlock'
import { TransactionsBlock } from './TransactionsBlock'

export default withAuth(function DashboardScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Dashboard')

  const goals = useAppSelector(selectGoals)
  const { name: username } = useAppSelector(selectUser)
  const categories = useAppSelector(selectCategories)
  const budgetLimit = useAppSelector(selectBudgetLimit)
  const isLoading = useAppSelector(selectIsDashboardLoading)

  const ButtonsBlock = useMemo<IconButtonItem[]>(
    () => [
      {
        Icon: <BudgetIcon />,
        title: translate('Buttons.Budget.title'),
        subtitle: translate('Buttons.Budget.subtitle'),
        path: '/settings/budget',
      },
      {
        Icon: <GoalIcon />,
        title: translate('Buttons.Goals.title'),
        subtitle: translate('Buttons.Goals.subtitle'),
        path: '/goals',
      },
      {
        Icon: <ProfileIcon />,
        title: translate('Buttons.Profile.title'),
        subtitle: translate('Buttons.Profile.subtitle'),
        path: '/settings/profile',
      },
      {
        Icon: <SecurityIcon />,
        title: translate('Buttons.Security.title'),
        subtitle: translate('Buttons.Security.subtitle'),
        path: '/settings/security',
      },
    ],
    [translate],
  )

  useEffect(() => {
    dispatch(getDashboardData())
  }, [dispatch])

  const title = translate('greeting', { name: username })

  return (
    <ScreenContent isLoading={isLoading} ContentSkeleton={DashboardScreenSkeleton} title={title}>
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={2}
        alignItems={{ xs: 'stretch', md: 'flex-start' }}
      >
        <Stack spacing={2}>
          <GoalsBlock goals={goals}></GoalsBlock>

          <BudgetBlock categories={categories} budgetLimit={budgetLimit} />
        </Stack>

        <Stack spacing={2} sx={{ flex: { md: '1 1 0%' }, maxWidth: '920px' }}>
          {/* <SearchBar/> */}

          {/* <StoriesBlock/> */}

          <IconButtonsBlock buttons={ButtonsBlock.slice(0, 2)} />

          <TransactionsBlock categories={categories} />

          <IconButtonsBlock buttons={ButtonsBlock.slice(2, 4)} />
        </Stack>
      </Stack>
    </ScreenContent>
  )
})
