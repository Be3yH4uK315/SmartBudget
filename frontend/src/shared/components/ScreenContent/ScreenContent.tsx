import { ComponentType, PropsWithChildren } from 'react'
import { ArrowBackOutlined } from '@mui/icons-material'
import { Container, IconButton, SkeletonProps, SxProps, Typography } from '@mui/material'
import { ScrollToTop } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useNavigate } from 'react-router'
import { ScreenSkeleton } from './ScreenSkeleton'

type Props = PropsWithChildren<{
  title?: string
  noScrollButton?: boolean
  ContentSkeleton?: ComponentType<SkeletonProps>
  isLoading?: boolean
  isBackButton?: boolean
  containerSx?: SxProps
}>

export const ScreenContent = ({
  title,
  containerSx,
  ContentSkeleton,
  children,
  isLoading = false,
  isBackButton = false,
  noScrollButton = false,
}: Props) => {
  const navigate = useNavigate()
  const translate = useTranslate('ScreenContentComponent')

  const handleClose = () => {
    navigate(-1)
  }

  return (
    <Container
      maxWidth={'lg'}
      sx={{
        display: 'flex',
        position: 'relative',
        flexDirection: 'column',
        flex: 1,
        pt: 4,
        overflow: 'visible',
        ...containerSx,
      }}
    >
      {isLoading ? (
        <ScreenSkeleton>{ContentSkeleton}</ScreenSkeleton>
      ) : (
        <>
          {isBackButton && (
            <IconButton
              onClick={handleClose}
              sx={{
                display: 'flex',
                justifyContent: 'flex-start',
                width: 'max-content',
                borderRadius: '6px',
                gap: 1,
                left: -10,
                color: 'text.primary',
              }}
            >
              <ArrowBackOutlined />

              <Typography>{translate('goBack')}</Typography>
            </IconButton>
          )}

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
