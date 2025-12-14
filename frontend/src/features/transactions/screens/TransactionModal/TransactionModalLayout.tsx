import { Dialog, DialogContent } from '@mui/material'
import { withAuth } from '@shared/components'
import { Outlet } from 'react-router'

export default withAuth(function TransactionModalLayout() {
  return (
    <Dialog open fullScreen>
      <DialogContent sx={{ maxWidth: '800px', width: '100%', position: 'relative', mx: 'auto' }}>
        <Outlet />
      </DialogContent>
    </Dialog>
  )
})
