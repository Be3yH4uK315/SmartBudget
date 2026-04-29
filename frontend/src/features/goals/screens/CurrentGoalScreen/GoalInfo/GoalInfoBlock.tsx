import { GoalChip } from '@features/goals/components'
import { GoalStatus } from '@features/goals/types'
import { AccessTimeOutlined, FlagOutlined } from '@mui/icons-material'
import { Stack, Typography } from '@mui/material'
import { StyledPaper, TypographyWithAdornment } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { formatCurrency } from '@shared/utils'
import dayjs from 'dayjs'
import { ExpiredBlockAlert } from './ExpiredAlertBlock'

type Props = {
  name: string
  finishDate: string | null
  status: GoalStatus
  isArchived: boolean
  targetValue: number
  currentValue: number
}
export const GoalInfoBlock = ({
  name,
  finishDate,
  status,
  isArchived,
  targetValue,
  currentValue,
}: Props) => {
  const translate = useTranslate('CurrentGoal')

  return (
    <StyledPaper>
      <Stack spacing={2}>
        <Stack
          direction={{ xs: 'column', sm: 'row', md: 'column' }}
          spacing={1}
          sx={{
            alignItems: { xs: 'normal', sm: 'center', md: 'normal' },
            justifyContent: { xs: 'normal', sm: 'space-between', md: 'normal' },
          }}
        >
          <Typography variant="h4">{name}</Typography>

          <Stack direction={'row'} spacing={1}>
            {isArchived && <GoalChip variant="archive" isArchived={isArchived} />}

            <GoalChip status={status} />
          </Stack>
        </Stack>

        {!finishDate && status !== 'achieved' && (
          <TypographyWithAdornment
            Icon={FlagOutlined}
            text={translate('targetValue', {
              value: formatCurrency(Math.max(targetValue - currentValue, 0)),
            })}
          />
        )}

        {finishDate && (
          <TypographyWithAdornment
            Icon={AccessTimeOutlined}
            text={translate('finishDate', {
              value: dayjs(finishDate).format('D MMMM YYYY'),
            })}
          />
        )}

        {status === 'expired' && <ExpiredBlockAlert />}
      </Stack>
    </StyledPaper>
  )
}
