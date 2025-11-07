import { Suspense } from 'react'
import { Route } from 'react-router'
import { AuthScreen, RegistrationScreen, ResetPasswordScreen } from './AuthScreen'

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
