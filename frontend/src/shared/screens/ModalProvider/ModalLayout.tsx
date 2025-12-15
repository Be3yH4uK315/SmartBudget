import { ReactNode } from 'react'
import { Dialog, DialogContent } from '@mui/material'

type Props = {
  children: ReactNode
}

export const ModalLayout = ({ children }: Props) => {
  return (
    <Dialog open fullScreen>
      <DialogContent sx={{ maxWidth: '800px', width: '100%', position: 'relative', mx: 'auto' }}>
        {children}
      </DialogContent>
    </Dialog>
  )
}
