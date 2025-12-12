import { dashboardRoutes } from '@features/dashboard/routes'
import { authRoutes } from '@shared/screens'
import { Route, Routes, useLocation } from 'react-router'

export const PageRouter = () => {
  const location = useLocation()
  const state = location.state as { backgroundLocation?: Location }

  return (
    <Routes location={state?.backgroundLocation || location}>
      <Route path="/" />

      {authRoutes.pages}

      {dashboardRoutes.pages}
    </Routes>
  )
}
