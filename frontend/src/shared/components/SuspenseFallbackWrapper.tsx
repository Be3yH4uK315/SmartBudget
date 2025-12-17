import { JSX, ReactNode, Suspense } from 'react'
import { Container } from '@mui/material'

type Props = {
  Fallback?: JSX.Element
  children: ReactNode
}

export const SuspenseFallbackWrapper = ({ Fallback, children }: Props) => {
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
