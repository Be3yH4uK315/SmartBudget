import { JSX, ReactNode, Suspense } from 'react'
import { Container } from '@mui/material'
import { LoadingScreen } from '@shared/screens/LoadingScreen'

type Props = {
  Fallback?: JSX.Element
  children: ReactNode
}

export const SuspenseFallbackWrapper = ({ Fallback = <LoadingScreen />, children }: Props) => {
  return (
    <Suspense
      fallback={
        <Container maxWidth="lg" sx={{ pt: 4 }}>
          {Fallback}
        </Container>
      }
    >
      {children}
    </Suspense>
  )
}
