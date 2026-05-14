import { Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { formatPercent } from '@shared/utils'

type Props = {
  currentAmount: number
  targetAmount: number
}

export const ProgressBlock = ({ currentAmount, targetAmount }: Props) => {
  const translate = useTranslate('CurrentGoal.ProgressBlock')

  return (
    <StyledPaper>
      <Typography variant="h4">{formatPercent(currentAmount / targetAmount)}</Typography>

      <Typography variant="h6">{translate('title')}</Typography>

      <Typography>{translate('subtitle')}</Typography>
    </StyledPaper>
  )
}
