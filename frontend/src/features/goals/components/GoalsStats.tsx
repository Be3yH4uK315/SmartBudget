import React from 'react'
import { Paper, Stack, Typography } from '@mui/material'
import { useTheme, useTranslate } from '@shared/hooks'
import { formatCurrency, formatPercent } from '@shared/utils'

type Props = {
  targetValue: number
  currentValue: number

  daysLeft?: number
}

type BlockProps = {
  type: 'percent' | 'currency' | 'date'
  value: number
  label: string
}

export const GoalsStats = React.memo(({ targetValue, currentValue, daysLeft }: Props) => {
  const translate = useTranslate('Goals')

  const hasDays = typeof daysLeft === 'number'
  const remaining = Math.max(targetValue - currentValue, 0)
  const nextPeriod = hasDays ? Math.min(daysLeft, 30) : 0

  const payment = hasDays && daysLeft ? (remaining / daysLeft) * nextPeriod : remaining
  const paymentLabel =
    hasDays && daysLeft > 0
      ? translate('CurrentGoal.GoalStats.nextPayment', { count: nextPeriod })
      : translate('CurrentGoal.GoalStats.nextPayment')

  const dataBlocks: BlockProps[] = hasDays
    ? [
        {
          type: 'currency',
          value: payment,
          label: paymentLabel,
        },
        {
          type: 'currency',
          value: remaining,
          label: translate('CurrentGoal.GoalStats.targetValue'),
        },
        {
          type: 'date',
          value: daysLeft,
          label: translate('CurrentGoal.GoalStats.daysLeft'),
        },
      ]
    : [
        {
          type: 'percent',
          value: currentValue / targetValue,
          label: translate('GoalsStats.progress'),
        },
        {
          type: 'currency',
          value: currentValue,
          label: translate('GoalsStats.currentValue'),
        },
        {
          type: 'currency',
          value: targetValue,
          label: translate('GoalsStats.targetValue'),
        },
      ]

  return (
    <Stack spacing={2} direction={{ xs: 'column', md: 'row' }}>
      {dataBlocks.map((b, i) => (
        <StatBlock key={i} {...b} />
      ))}
    </Stack>
  )
})

const StatBlock = ({ type = 'currency', value, label }: BlockProps) => {
  const translate = useTranslate('Goals.CurrentGoal.GoalStats')
  const theme = useTheme()

  const formatters = {
    percent: formatPercent,
    currency: formatCurrency,
    date: (value: number) => translate('day', { count: value }),
  }

  const formattedValue = formatters[type](value)
  const captionColor = theme.colorMode === 'light' ? 'gray.main' : 'gray.light'

  return (
    <Paper
      elevation={2}
      sx={{
        px: 3,
        py: 2,
        display: 'flex',
        flex: 1,
        flexDirection: 'column',
        borderRadius: '24px',
        mx: 0,
      }}
    >
      <Typography variant="h5">{formattedValue}</Typography>

      <Typography color={captionColor}>{label}</Typography>
    </Paper>
  )
}
