import { ComponentType, PropsWithChildren } from 'react'
import { Container, SkeletonProps, SxProps, Typography } from '@mui/material'
import { ScrollToTop } from '../ScrollToTop'
import { ScreenSkeleton } from './ScreenSkeleton'

type Props = PropsWithChildren<{
  title?: string
  noScrollButton?: boolean
  ContentSkeleton?: ComponentType<SkeletonProps>
  isLoading?: boolean
  containerSx?: SxProps
}>

export const ScreenContent = ({
  title,
  containerSx,
  ContentSkeleton,
  children,
  isLoading = false,
  noScrollButton = false,
}: Props) => {
  return (
    <Container
      maxWidth={'lg'}
      sx={{ display: 'flex', flexDirection: 'column', flex: 1, pt: 4, ...containerSx }}
    >
      {isLoading ? (
        <ScreenSkeleton>{ContentSkeleton}</ScreenSkeleton>
      ) : (
        <>
          {title && (
            <Typography
              noWrap
              title={title}
              sx={{
                typography: 'h3',
                marginBottom: 3,
              }}
            >
              {title}
            </Typography>
          )}

          {children}

          {!noScrollButton && <ScrollToTop />}
        </>
      )}
    </Container>
  )
}
