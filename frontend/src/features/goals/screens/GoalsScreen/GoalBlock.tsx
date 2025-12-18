import React from 'react'
import { STATUS_STYLES } from '@features/goals/constants/statusStyles'
import { Goal } from '@features/goals/types'
import { Box, Paper, Stack, Typography, useTheme } from '@mui/material'
import { PieChartWithCenterLabel } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { CenterLabel, PieDataItem } from '@shared/types/components'
import { formatCurrency } from '@shared/utils'
import dayjs from 'dayjs'
import { useNavigate } from 'react-router'

type Props = {
  goal: Goal
}

export const GoalBlock = React.memo(({ goal }: Props) => {
  const translate = useTranslate('Goals.GoalBlock')
  const navigate = useNavigate()
  const theme = useTheme()

  const { goalId, name, targetValue, currentValue, finishDate, status } = goal

  const { borderColor, statusColor, pieColor } = STATUS_STYLES[status](theme)

  const pieData: PieDataItem[] = [
    { value: targetValue, label: '1', color: pieColor },
    { value: targetValue - currentValue, label: '2', color: theme.palette.grayButton.dark },
  ]
  console.log(pieData)

  const centerLabel: CenterLabel = {
    type: 'percent',
    value: currentValue / targetValue,
  }

  return (
    <Paper
      onClick={() => navigate(`./${goalId}`)}
      sx={{
        height: 'min-content',
        py: 2,
        px: 3,
        borderRadius: '24px',
        cursor: 'pointer',
        bgcolor: theme.palette.surface.light,
        border: '2px solid',
        borderColor: borderColor,
      }}
      elevation={2}
    >
      <Stack direction={'row'} sx={{ justifyContent: 'space-between' }}>
        <Stack>
          <Stack p={0} m={0}>
            <Typography variant="h5">{name}</Typography>

            <Typography variant="caption" color={statusColor}>
              {translate(status)}
            </Typography>
          </Stack>

          <Stack>
            <Typography>
              {translate('currentValue')}
              {formatCurrency(currentValue)}
            </Typography>

            <Typography>
              {translate('achieveValue')}
              {formatCurrency(targetValue - currentValue)}
            </Typography>

            <Typography>
              {translate('finishDate')}
              {dayjs(finishDate).format('D MMMM YYYY')}
            </Typography>
          </Stack>
        </Stack>

        <Box sx={{ width: 'min-content' }}>
          <PieChartWithCenterLabel
            pieData={pieData}
            innerRadius={45}
            width={120}
            height={120}
            centerLabel={centerLabel}
          />
        </Box>
      </Stack>
    </Paper>
  )
})
