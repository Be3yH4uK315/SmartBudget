import { ComponentType, PropsWithChildren } from 'react'
import { Container, SkeletonProps, SxProps } from '@mui/material'
import { ScrollToTop } from '../ScrollToTop'
import { ScreenSkeleton } from './ScreenSkeleton'

type Props = PropsWithChildren<{
  noScrollButton?: boolean
  ContentSkeleton?: ComponentType<SkeletonProps>
  isLoading?: boolean
  containerSx?: SxProps
}>

export const ScreenContent = ({
  containerSx,
  ContentSkeleton,
  children,
  isLoading = false,
  noScrollButton = false,
}: Props) => {
  return (
    <Container sx={{ display: 'flex', flexDirection: 'column', flex: 1, pt: 4, ...containerSx }}>
      {isLoading ? (
        <ScreenSkeleton>{ContentSkeleton}</ScreenSkeleton>
      ) : (
        <>
          {children}

          {!noScrollButton && <ScrollToTop />}
        </>
      )}
    </Container>
  )
}
