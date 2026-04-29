import { Stack, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'

type Props = {
  title: string
  subtitle?: string
  value?: number
}

export const InfoBlock = ({ title, subtitle, value }: Props) => {
  return (
    <StyledPaper>
      <Stack>
        <Typography variant="h5">{title}</Typography>

        {subtitle && <Typography>{subtitle}</Typography>}

        {value && <Typography>{value}</Typography>}
      </Stack>
    </StyledPaper>
  )
}
