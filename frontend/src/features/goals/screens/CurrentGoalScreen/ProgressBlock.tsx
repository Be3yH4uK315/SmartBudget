import { Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { formatPercent } from '@shared/utils'

type Props = {
  currentValue: number
  targetValue: number
}

export const ProgressBlock = ({ currentValue, targetValue }: Props) => {
  const translate = useTranslate('CurrentGoal.ProgressBlock')

  return (
    <StyledPaper>
      <Typography variant="h4">{formatPercent(currentValue / targetValue)}</Typography>

      <Typography variant="h6">{translate('title')}</Typography>

      <Typography>{translate('subtitle')}</Typography>
    </StyledPaper>
  )
}
