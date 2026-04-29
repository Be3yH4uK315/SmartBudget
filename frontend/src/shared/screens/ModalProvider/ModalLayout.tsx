import { ReactNode } from 'react'
import { Dialog, DialogContent, SxProps } from '@mui/material'
import { withAuth } from '@shared/components/hocs'

type Props = {
  children: ReactNode
  contentSx?: SxProps
}

export default function ModalLayout({ children, contentSx }: Props) {
  return (
    <Dialog open fullScreen>
      <DialogContent
        sx={{ maxWidth: '800px', width: '100%', position: 'relative', mx: 'auto', ...contentSx }}
      >
        {children}
      </DialogContent>
    </Dialog>
  )
}
