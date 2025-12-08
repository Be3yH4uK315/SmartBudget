import { useEffect, useMemo } from 'react'
import {
  BudgetBlock,
  DashboardScreenSkeleton,
  GoalsBlock,
  TransactionsBlock,
} from '@features/dashboard/screens'
import {
  getDashboardData,
  selectBudgetLimit,
  selectCategories,
  selectGoals,
  selectIsDashboardLoading,
} from '@features/dashboard/store'
import { Stack } from '@mui/material'
import { BudgetIcon, GoalIcon, ProfileIcon, SecurityIcon } from '@shared/assets/icons'
import { IconButtonsBlock, ScreenContent, withAuth } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { selectUser, useAppDispatch, useAppSelector } from '@shared/store'

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

  return (
    <ScreenContent
      isLoading={isLoading}
      ContentSkeleton={DashboardScreenSkeleton}
      title={translate('greeting', { name: username })}
    >
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
