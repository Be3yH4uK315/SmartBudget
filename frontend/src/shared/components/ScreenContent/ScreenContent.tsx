import { ComponentType, JSX, PropsWithChildren } from 'react'
import { ArrowBackOutlined, InfoOutlined } from '@mui/icons-material'
import { Container, IconButton, SkeletonProps, Stack, SxProps, Typography } from '@mui/material'
import { ScrollToTop, StyledTooltip } from '@shared/components'
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
  InfoBlock?: JSX.Element
}>

export const ScreenContent = ({
  title,
  containerSx,
  ContentSkeleton,
  children,
  isLoading = false,
  isBackButton = false,
  noScrollButton = false,
  InfoBlock,
}: Props) => {
  const navigate = useNavigate()
  const translate = useTranslate('ScreenContentComponent')

  const handleClose = () => {
    navigate(-1)
  }

  const containerPaddingTop = isBackButton ? 2 : 4
  const titleMarginTop = isBackButton ? 1 : 0

  return (
    <Container
      maxWidth={'lg'}
      sx={{
        display: 'flex',
        position: 'relative',
        flexDirection: 'column',
        flex: 1,
        pt: containerPaddingTop,
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
            <Stack
              direction={'row'}
              spacing={2}
              sx={{
                maxWidth: 'max-content',
                mt: titleMarginTop,
                mb: 3,
                alignItems: 'center',
              }}
            >
              <Typography
                noWrap
                title={title}
                sx={{
                  typography: 'h3',
                }}
              >
                {title}
              </Typography>

              {InfoBlock && (
                <StyledTooltip title={InfoBlock}>
                  <InfoOutlined />
                </StyledTooltip>
              )}
            </Stack>
          )}

          {children}

          {!noScrollButton && <ScrollToTop />}
        </>
      )}
    </Container>
  )
}
