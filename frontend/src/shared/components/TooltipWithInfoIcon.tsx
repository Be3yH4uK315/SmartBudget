import { InfoOutlined } from '@mui/icons-material'
import { SxProps } from '@mui/material'
import { StyledTooltip } from './StyledTooltip'

type Props = {
  title: React.ReactNode
  iconSx?: SxProps
}

export const TooltipWithInfoIcon = ({ title, iconSx }: Props) => {
  return (
    <StyledTooltip title={title}>
      <InfoOutlined
        sx={{ color: 'secondary.main', ':hover': { color: 'secondary.light' }, ...iconSx }}
      />
    </StyledTooltip>
  )
}
