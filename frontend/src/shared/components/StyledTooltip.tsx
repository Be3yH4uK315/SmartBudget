import { ReactElement, ReactNode, useState } from 'react'
import { Tooltip } from '@mui/material'

type Props = {
  title: ReactNode
  children: ReactElement
}

export const StyledTooltip = ({ title, children }: Props) => {
  const [open, setOpen] = useState<boolean>(false)

  return (
    <Tooltip
      title={title}
      open={open}
      onOpen={() => setOpen(true)}
      onClose={() => setOpen(false)}
      enterTouchDelay={0}
      leaveTouchDelay={5000}
    >
      {children}
    </Tooltip>
  )
}
