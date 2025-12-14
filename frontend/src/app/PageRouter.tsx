import { dashboardRoutes } from '@features/dashboard/routes'
import { transactionsRoutes } from '@features/transactions/routes'
import { authRoutes } from '@shared/screens'
import { matchPath, Navigate, Route, Routes, useLocation } from 'react-router'

export const PageRouter = () => {
  const location = useLocation()
  const state = location.state as { backgroundLocation?: Location }

  const modalPaths = ['/transactions/:id', '/transactions/category/:id']

  const isModalPath = modalPaths.some((p) => matchPath({ path: p, end: true }, location.pathname))

  if (isModalPath && !state?.backgroundLocation) {
    const parentPath = location.pathname.replace(/\/[^/]+$/, '')
    return <Navigate to={parentPath} replace />
  }

  return (
    <>
      <Routes location={state?.backgroundLocation || location}>
        <Route path="/">
          {authRoutes.pages}

          {dashboardRoutes.pages}

          {transactionsRoutes.pages}
        </Route>
      </Routes>

      {state?.backgroundLocation && <Routes>{transactionsRoutes.modals}</Routes>}
    </>
  )
}
