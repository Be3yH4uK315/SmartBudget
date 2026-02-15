import { ErrorOutlineOutlined } from '@mui/icons-material'
import { Typography } from '@mui/material'
import { StyledPaper, TypographyWithAdornment } from '@shared/components'
import { useTranslate } from '@shared/hooks'

export const ExpiredBlockAlert = () => {
  const translate = useTranslate('CurrentGoal.ExpiredBlock')

  return (
    <StyledPaper
      paperSx={{ border: '2px solid', borderColor: 'error.main', bgcolor: 'error.dark' }}
      noElevation
    >
      <TypographyWithAdornment
        Icon={ErrorOutlineOutlined}
        iconSize="medium"
        text={translate('title')}
        typographyVariant="h4"
        typographySx={{ color: '#fff' }}
        color="#fff"
      />

      <Typography color="#fff">{translate('subtitle')}</Typography>
    </StyledPaper>
  )
}
