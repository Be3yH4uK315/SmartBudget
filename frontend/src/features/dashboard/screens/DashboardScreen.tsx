import { useEffect, useMemo } from 'react'
import { BudgetBlock, DashboardScreenSkeleton, GoalsBlock } from '@features/dashboard/screens'
import {
  clearDashboardState,
  getDashboardBudget,
  getDashboardGoals,
  selectBudgetLimit,
  selectCategories,
  selectGoals,
  selectIsDashboardBudgetLoading,
  selectIsDashboardGoalsLoading,
} from '@features/dashboard/store'
import {
  AccountBalanceWalletOutlined,
  LockOutlined,
  NotificationsOutlined,
  OutlinedFlagOutlined,
} from '@mui/icons-material'
import { Stack } from '@mui/material'
import { IconButtonsBlock, ScreenContent, TransactionsPieBlock, withAuth } from '@shared/components'
import { ROUTES } from '@shared/constants'
import { useTransactionFilters, useTranslate } from '@shared/hooks'
import { selectUser, useAppDispatch, useAppSelector } from '@shared/store'
import { IconButtonItem } from '@shared/types'
import { CenterLabel } from '@shared/types/components'
import { mapDashboardCategory } from '@shared/utils'
import dayjs from 'dayjs'

export default function DashboardScreen() {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Dashboard')
  const translateMonth = useTranslate('Month')

  const goals = useAppSelector(selectGoals)
  const { name: username } = useAppSelector(selectUser)
  const categories = useAppSelector(selectCategories)
  const budgetLimit = useAppSelector(selectBudgetLimit)
  const isBudgetLoading = useAppSelector(selectIsDashboardBudgetLoading)
  const isGoalsLoading = useAppSelector(selectIsDashboardGoalsLoading)

  const ButtonsBlock = useMemo<IconButtonItem[]>(
    () => [
      {
        Icon: <AccountBalanceWalletOutlined />,
        title: translate('Buttons.Budget.title'),
        subtitle: translate('Buttons.Budget.subtitle'),
        path: ROUTES.PAGES.SETTINGS.BUDGET,
      },
      {
        Icon: <OutlinedFlagOutlined />,
        title: translate('Buttons.Goals.title'),
        subtitle: translate('Buttons.Goals.subtitle'),
        path: ROUTES.PAGES.GOALS.MAIN,
      },
      {
        Icon: <NotificationsOutlined />,
        title: translate('Buttons.Notifications.title'),
        subtitle: translate('Buttons.Notifications.subtitle'),
        path: ROUTES.PAGES.NOTIFICATIONS,
      },
      {
        Icon: <LockOutlined />,
        title: translate('Buttons.Security.title'),
        subtitle: translate('Buttons.Security.subtitle'),
        path: ROUTES.PAGES.SETTINGS.SECURITY,
      },
    ],
    [translate],
  )

  const { activeType, toggleFilter, normalizedData, total } = useTransactionFilters(
    categories,
    mapDashboardCategory,
    'expense',
  )

  const transactionsBlockTitle = `${translate('TransactionsPieBlock.title')} ${translateMonth(`${dayjs().month()}`)}`

  const centerLabel: CenterLabel = {
    type: 'amount',
    total: total,
    label: translate(`TransactionsPieBlock.${activeType}`).toLowerCase(),
  }

  useEffect(() => {
    dispatch(getDashboardBudget())
    dispatch(getDashboardGoals())

    return () => {
      dispatch(clearDashboardState())
    }
  }, [dispatch])

  return (
    <ScreenContent
      isLoading={isBudgetLoading || isGoalsLoading}
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
          <IconButtonsBlock buttons={ButtonsBlock.slice(0, 2)} />

          <TransactionsPieBlock
            title={transactionsBlockTitle}
            activeType={activeType}
            pieData={normalizedData}
            centerLabel={centerLabel}
            toggleFilter={toggleFilter}
          />

          <IconButtonsBlock buttons={ButtonsBlock.slice(2, 4)} />
        </Stack>
      </Stack>
    </ScreenContent>
  )
}
