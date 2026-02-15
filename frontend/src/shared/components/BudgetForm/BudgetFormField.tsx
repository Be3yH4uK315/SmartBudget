import { Stack, Typography } from '@mui/material'
import { StyledPaper, TooltipWithInfoIcon } from '@shared/components'

type Props = {
  title: string
  subtitle?: string
  tooltip?: string
  titleSpacing?: number
  children: React.ReactNode
}

export const BudgetFormField = ({
  title,
  subtitle,
  tooltip,
  titleSpacing = 2,
  children,
}: Props) => {
  return (
    <StyledPaper noElevation>
      <Stack spacing={titleSpacing} display={'flex'}>
        <Stack>
          <Stack
            direction={'row'}
            alignItems={'center'}
            spacing={2}
            justifyContent={'space-between'}
          >
            <Typography variant="h4">{title}</Typography>

            {tooltip && <TooltipWithInfoIcon title={tooltip} />}
          </Stack>

          {subtitle && <Typography variant="caption">{subtitle}</Typography>}
        </Stack>

        {children}
      </Stack>
    </StyledPaper>
  )
}
