import { CloseOutlined } from '@mui/icons-material'
import { IconButton } from '@mui/material'

type Props = {
  onClose: () => void
}

export const CloseModalButton = ({ onClose }: Props) => {
  return (
    <IconButton onClick={onClose} sx={{ position: 'absolute', top: 12, right: 12 }}>
      <CloseOutlined sx={{ color: 'link.main' }} />
    </IconButton>
  )
}
