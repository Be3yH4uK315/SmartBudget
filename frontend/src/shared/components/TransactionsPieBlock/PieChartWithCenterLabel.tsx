import React, { useMemo } from 'react'
import { styled, useTheme } from '@mui/material'
import { PieChart, useDrawingArea } from '@mui/x-charts'
import { CenterLabel, PieDataItem } from '@shared/types/components'
import { formatCurrency, formatPercent } from '@shared/utils'

type Props = {
  pieData: PieDataItem[]
  innerRadius?: number
  width?: number
  height?: number
  centerLabel: CenterLabel
}

export const PieChartWithCenterLabel = React.memo(function PieChartWithCenterLabel({
  pieData,
  innerRadius = 60,
  width,
  height,
  centerLabel,
}: Props) {
  const data = useMemo<Omit<PieDataItem, 'lightColor'>[]>(
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    () => pieData.map(({ lightColor, ...rest }) => rest),
    [pieData],
  )

  return (
    <PieChart
      slots={{ tooltip: () => null }}
      hideLegend
      series={[{ data, innerRadius }]}
      width={width}
      height={height}
      slotProps={{
        pieArc: {
          stroke: 'none',
          strokeWidth: 0,
        },
      }}
    >
      <PieCenterLabel centerLabel={centerLabel} />
    </PieChart>
  )
})

const StyledText = styled('text')(({ theme }) => ({
  fill: theme.palette.text.primary,
  textAnchor: 'middle',
  dominantBaseline: 'central',
}))

const PieCenterLabel = React.memo(({ centerLabel }: { centerLabel: CenterLabel }) => {
  const { width, height, left, top } = useDrawingArea()

  const amountTypography = useTheme().typography.h5
  const percentTypography = useTheme().typography.body1

  const x = left + width / 2
  const y = top + height / 2

  if (centerLabel.type === 'amount') {
    return (
      <StyledText x={x} y={y} sx={{ ...amountTypography }}>
        <tspan x={x} dy="-0.4em">
          {centerLabel.total > 0 ? formatCurrency(centerLabel.total) : ''}
        </tspan>
        <tspan x={x} dy="1.2em" style={{ fontSize: '0.7em' }}>
          {centerLabel.label}
        </tspan>
      </StyledText>
    )
  }

  return (
    <StyledText x={x} y={y} sx={{ ...percentTypography, fontWeight: 600 }}>
      {formatPercent(centerLabel.value)}
    </StyledText>
  )
})
