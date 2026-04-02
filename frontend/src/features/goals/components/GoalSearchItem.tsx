import { GoalSearchOption } from '@features/goals/types'
import { FlagOutlined, TaskAltOutlined } from '@mui/icons-material'
import { Stack, Typography, useTheme as useMUITheme } from '@mui/material'
import { PercentLine } from '@shared/components/PercentLine'
import { StyledPaper } from '@shared/components/StyledPaper'
import { TypographyWithAdornment } from '@shared/components/TypographyWithAdornment'
import { ROUTES } from '@shared/constants/routes'
import { useTheme, useTranslate } from '@shared/hooks'
import { formatCurrency } from '@shared/utils/formatCurrency'
import { useNavigate } from 'react-router'
import { STATUS_STYLES } from '../constants'
import { GoalChip } from './GoalChip'

type Props = {
  goal: GoalSearchOption
}

export const GoalSearchItem = ({ goal }: Props) => {
  const translate = useTranslate('Goals.GoalBlock')
  const navigate = useNavigate()
  const theme = useTheme()
  const muiTheme = useMUITheme()

  const { goalId, name, targetValue, currentValue, status, isArchived } = goal
  const hoverColor = theme.colorMode === 'light' ? 'surface.dark' : 'surface.main'

  const { pieColor } = STATUS_STYLES[status](muiTheme)

  return (
    <StyledPaper
      noElevation
      paperSx={{
        ':hover': { bgcolor: hoverColor },
        cursor: 'pointer',
        p: 2,
        px: 4,
        borderRadius: '12px',
      }}
      onClick={() => navigate(`${ROUTES.PAGES.GOALS.MAIN}/${goalId}`)}
    >
      <Stack spacing={1}>
        <Stack
          spacing={1}
          direction={{ xs: 'column', sm: 'row' }}
          sx={{ justifyContent: 'space-between' }}
        >
          <Stack
            spacing={1}
            sx={{
              alignItems: { xs: 'center', sm: 'normal' },
              justifyContent: { xs: 'center', sm: 'normal' },
              p: 0,
              m: 0,
            }}
          >
            <Typography variant="h5">{name}</Typography>

            <Stack direction={'row'} spacing={1}>
              <GoalChip status={status} />

              {isArchived && <GoalChip variant="archive" isArchived={isArchived} />}
            </Stack>
          </Stack>

          <Stack spacing={1}>
            <Stack spacing={1} alignItems={{ xs: 'center', sm: 'end' }}>
              <TypographyWithAdornment
                Icon={TaskAltOutlined}
                text={translate('currentValue', { value: formatCurrency(currentValue) })}
              />

              {status !== 'achieved' && (
                <TypographyWithAdornment
                  Icon={FlagOutlined}
                  text={translate('targetValue', {
                    value: formatCurrency(Math.max(targetValue - currentValue, 0)),
                  })}
                />
              )}
            </Stack>
          </Stack>
        </Stack>

        <PercentLine limit={targetValue} currentValue={currentValue} color={pieColor} />
      </Stack>
    </StyledPaper>
  )
}
