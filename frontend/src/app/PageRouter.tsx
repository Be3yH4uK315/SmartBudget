import { budgetRoutes } from '@features/budget/routes'
import { dashboardRoutes } from '@features/dashboard/routes'
import { notificationsRoutes } from '@features/notifications/routes'
import { settingsRoutes } from '@features/settings/routes'
import { transactionsRoutes } from '@features/transactions/routes'
import { authRoutes } from '@shared/screens'
import { PublicPage } from '@shared/screens/PublicPage'
import { UndefinedScreen } from '@shared/screens/UndefinedScreen'
import { Route, Routes, useLocation } from 'react-router'
import { goalsRoutes } from 'src/features/goals/routes'

export const PageRouter = () => {
  const location = useLocation()
  const state = location.state as { backgroundLocation?: Location }

  return (
    <Routes location={state?.backgroundLocation || location}>
      <Route path="/">
        <Route index element={<PublicPage />} />

        {authRoutes.pages}

        {dashboardRoutes.pages}

        {transactionsRoutes.pages}

        {goalsRoutes.pages}

        {settingsRoutes.pages}

        {budgetRoutes.pages}

        {notificationsRoutes.pages}
      </Route>

      <Route path="*" element={<UndefinedScreen />} />
    </Routes>
  )
}
