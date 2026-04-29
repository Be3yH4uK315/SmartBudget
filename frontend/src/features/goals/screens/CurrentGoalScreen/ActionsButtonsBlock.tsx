import { GoalStatus } from '@features/goals/types'
import {
  ArchiveOutlined,
  CancelOutlined,
  RestoreOutlined,
  UnarchiveOutlined,
} from '@mui/icons-material'
import { Button, Stack } from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props = {
  status: GoalStatus
  isArchived: boolean
  onStatusClick: () => void
  onArchivedClick: () => void
}

export const ActionsButtonsBlock = ({
  status,
  isArchived,
  onStatusClick,
  onArchivedClick,
}: Props) => {
  const translate = useTranslate('CurrentGoal.ActionsButtonsBlock')

  const shouldRenderStatusButton = status !== 'achieved' && !isArchived
  const shouldRenderArchiveButton = status === 'closed' || status === 'achieved'

  const ArchiveIcon = isArchived ? ArchiveOutlined : UnarchiveOutlined
  const StatusIcon = status === 'closed' ? RestoreOutlined : CancelOutlined

  const archiveButtonTitle = !isArchived ? 'archive' : 'unarchive'
  const statusButtonTitle = status === 'closed' ? 'buttonRestore' : 'buttonClose'

  return (
    <Stack spacing={2}>
      {shouldRenderArchiveButton && (
        <Button startIcon={<ArchiveIcon />} onClick={onArchivedClick}>
          {translate(archiveButtonTitle)}
        </Button>
      )}

      {shouldRenderStatusButton && (
        <Button startIcon={<StatusIcon />} onClick={onStatusClick}>
          {translate(statusButtonTitle)}
        </Button>
      )}
    </Stack>
  )
}
