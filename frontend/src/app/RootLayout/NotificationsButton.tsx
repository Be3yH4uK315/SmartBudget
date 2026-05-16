import { NotificationsOutlined } from '@mui/icons-material'
import { Badge, IconButton } from '@mui/material'
import { ROUTES } from '@shared/constants'
import { selectUser, useAppSelector } from '@shared/store'
import { useNavigate } from 'react-router'

export const NotificationsButton = () => {
  const navigate = useNavigate()
  const unreadCount = useAppSelector(selectUser).unreadCount

  return (
    <IconButton
      size="large"
      onClick={() => navigate(ROUTES.PAGES.NOTIFICATIONS)}
      sx={{
        borderRadius: 1,
      }}
    >
      <Badge badgeContent={unreadCount} max={9} color={'error'}>
        <NotificationsOutlined sx={{ color: 'gray.main' }} />
      </Badge>
    </IconButton>
  )
}
