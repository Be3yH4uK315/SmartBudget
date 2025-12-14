import { Dialog, DialogContent } from '@mui/material'
import { Outlet } from 'react-router'

const TransactionModalLayout = () => {
  return (
    <Dialog open fullScreen>
      <DialogContent sx={{ maxWidth: '800px', width: '100%', position: 'relative', mx: 'auto' }}>
        <Outlet />
      </DialogContent>
    </Dialog>
  )
}

export default TransactionModalLayout
