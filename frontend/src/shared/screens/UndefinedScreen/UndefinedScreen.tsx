import { Box, Button, Stack, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components/StyledPaper'
import { ROUTES } from '@shared/constants/routes'
import { useTranslate } from '@shared/hooks'
import { useNavigate } from 'react-router'

export const UndefinedScreen = () => {
  const translate = useTranslate('UndefinedScreen')
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        width: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        p: 2,
      }}
    >
      <StyledPaper noElevation paperSx={{ maxWidth: '600px', p: 4 }}>
        <Stack spacing={3}>
          <Stack textAlign={'center'}>
            <Typography variant="h1" fontSize={'8rem'} color="primary.main">
              404
            </Typography>

            <Typography variant="h1" fontSize={'3rem'}>
              {translate('title')}
            </Typography>

            <Typography>{translate('subtitle')}</Typography>
          </Stack>

          <Button
            variant="yellow"
            onClick={() => navigate(ROUTES.PAGES.PUBLIC_PAGE, { replace: true })}
          >
            {translate('button')}
          </Button>
        </Stack>
      </StyledPaper>
    </Box>
  )
}
