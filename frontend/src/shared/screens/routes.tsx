import { lazy, Suspense } from 'react'
import { Route } from 'react-router'

const AuthScreen = lazy(() => import('./AuthScreen/AuthScreen'))
const RegistrationScreen = lazy(() => import('./AuthScreen/RegistrationScreen'))
const ResetPasswordScreen = lazy(() => import('./AuthScreen/ResetPasswordScreen'))

export const authRoutes = {
  pages: (
    <Route path="auth">
      <Route
        path="sign-in"
        index
        element={
          <Suspense>
            <AuthScreen />
          </Suspense>
        }
      />

      <Route
        path="registration"
        index
        element={
          <Suspense>
            <RegistrationScreen />
          </Suspense>
        }
      />

      <Route
        path="reset-password"
        index
        element={
          <Suspense>
            <ResetPasswordScreen />
          </Suspense>
        }
      />
    </Route>
  ),
}
