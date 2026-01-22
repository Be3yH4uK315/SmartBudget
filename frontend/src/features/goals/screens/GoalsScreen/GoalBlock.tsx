import React from 'react'
import { GoalChip } from '@features/goals/components'
import { GoalTagsBlock } from '@features/goals/components/GoalTags'
import { STATUS_STYLES } from '@features/goals/constants/statusStyles'
import { SimplifiedGoal } from '@features/goals/types'
import { AccessTimeOutlined, FlagOutlined, TaskAltOutlined } from '@mui/icons-material'
import { Box, Divider, Stack, Typography, useMediaQuery, useTheme } from '@mui/material'
import {
  PercentLine,
  PieChartWithCenterLabel,
  StyledPaper,
  TypographyWithAdornment,
} from '@shared/components'
import { ROUTES } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { CenterLabel, PieDataItem } from '@shared/types/components'
import { formatCurrency } from '@shared/utils'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router'

type Props = {
  goal: SimplifiedGoal
}

export const GoalBlock = React.memo(({ goal }: Props) => {
  const translate = useTranslate('Goals.GoalBlock')
  const navigate = useNavigate()
  const theme = useTheme()

  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  const {
    goalId,
    name,
    targetValue,
    currentValue,
    finishDate,
    status,
    tags,
    priority,
    isArchived,
  } = goal

  const { pieColor } = STATUS_STYLES[status](theme)

  const width = isMobile ? '100%' : 'auto'

  const pieData: PieDataItem[] = [
    { value: currentValue, color: pieColor },
    { value: Math.max(targetValue - currentValue, 0), color: theme.palette.grayButton.dark },
  ]

  const centerLabel: CenterLabel = {
    type: 'percent',
    value: currentValue / targetValue,
  }

  return (
    <StyledPaper
      role="button"
      onClick={() => navigate(`${ROUTES.PAGES.GOALS.MAIN}/${goalId}`)}
      paperSx={{
        cursor: 'pointer',
      }}
    >
      <Stack spacing={1}>
        <GoalTagsBlock tags={tags} priority={priority} />

        <Stack direction={'row'} sx={{ justifyContent: 'space-between' }}>
          <Stack spacing={1} sx={{ width: width }}>
            <Stack direction={'row'} spacing={1} sx={{ alignItems: 'center', p: 0, m: 0 }}>
              <Typography variant="h5">{name}</Typography>

              <Stack direction={'row'} spacing={1}>
                <GoalChip status={status} />

                {isArchived && <GoalChip variant="archive" isArchived={isArchived} />}
              </Stack>
            </Stack>

            <Stack spacing={1}>
              <Stack>
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

              {finishDate && (
                <>
                  <Divider sx={{ bgcolor: 'text.primary' }} />

                  <TypographyWithAdornment
                    Icon={AccessTimeOutlined}
                    text={translate('finishDate', {
                      value: dayjs(finishDate).format('D MMMM YYYY'),
                    })}
                  />
                </>
              )}

              {isMobile && (
                <>
                  <Divider sx={{ bgcolor: 'text.primary' }} />

                  <PercentLine limit={targetValue} currentValue={currentValue} color={pieColor} />
                </>
              )}
            </Stack>
          </Stack>

          {!isMobile && (
            <Box sx={{ width: 'min-content' }}>
              <PieChartWithCenterLabel
                pieData={pieData}
                innerRadius={45}
                width={120}
                height={120}
                centerLabel={centerLabel}
              />
            </Box>
          )}
        </Stack>
      </Stack>
    </StyledPaper>
  )
})
