import { Box, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

export const NoDataFallback = () => {
  const translate = useTranslate('Budget')
  return (
    <Box
      sx={{
        display: 'flex',
        width: '100%',
        height: '100%',
        alignItems: 'center',
        justifyContent: 'center',
        border: '2px dashed',
        borderColor: 'gray.main',
        borderRadius: '24px',
        flexDirection: 'column',
        p: 1,
      }}
    >
      <Typography variant="h5">{translate('cannotFindData')}</Typography>

      <Typography variant="caption" whiteSpace={'wrap'}>
        {translate('tryAgain')}
      </Typography>
    </Box>
  )
}
