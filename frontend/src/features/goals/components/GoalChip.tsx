import { STATUS_STYLES } from '@features/goals/constants/statusStyles'
import { GoalStatus } from '@features/goals/types'
import { Chip, useTheme } from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props = {
  status?: GoalStatus
  isArchived?: boolean
  variant?: 'tag' | 'archive'
}

export const GoalChip = ({ status, isArchived, variant = 'tag' }: Props) => {
  const translateStatus = useTranslate('GoalStatus')
  const theme = useTheme()

  if (status) {
    const { statusColor } = STATUS_STYLES[status](theme)

    return (
      <Chip
        sx={{ color: statusColor, borderColor: statusColor, width: 'max-content' }}
        label={translateStatus(status)}
        size="small"
        variant="outlined"
      />
    )
  }

  if (variant === 'archive' && isArchived) {
    return (
      <Chip
        sx={{ color: 'gray.main', borderColor: 'gray.main', width: 'max-content' }}
        label={translateStatus('archived')}
        size="small"
        variant="outlined"
      />
    )
  }
}
