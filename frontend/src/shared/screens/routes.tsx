import { lazy, Suspense } from 'react'
import { Container } from '@mui/material'
import { Route } from 'react-router'
import { LoadingScreen } from './LoadingScreen'

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
          <Suspense fallback={showFallback()}>
            <AuthScreen />
          </Suspense>
        }
      />

      <Route
        path="registration"
        index
        element={
          <Suspense fallback={showFallback()}>
            <RegistrationScreen />
          </Suspense>
        }
      />

      <Route
        path="reset-password"
        index
        element={
          <Suspense fallback={showFallback()}>
            <ResetPasswordScreen />
          </Suspense>
        }
      />
    </Route>
  ),
}

export function showFallback() {
  return (
    <Container maxWidth="lg" sx={{ pt: 4 }}>
      <LoadingScreen />
    </Container>
  )
}
