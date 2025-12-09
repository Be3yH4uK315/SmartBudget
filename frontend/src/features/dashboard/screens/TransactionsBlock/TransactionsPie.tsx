import React from 'react'
import { styled } from '@mui/material'
import { PieChart, useDrawingArea } from '@mui/x-charts'
import { normalizedCategory } from '@features/dashboard/types'

type Props = {
  data: Omit<normalizedCategory, 'lightColor'>[]
  total: number
  innerRadius?: number
  width?: number
  height?: number
  label: string
}

export const PieChartWithCenterLabel = React.memo(function PieChartWithCenterLabel({
  data,
  innerRadius = 60,
  total = 0,
  width,
  height,
  label,
}: Props) {
  if (!data.length) return null

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
      <PieCenterLabel label={label} total={total} />
    </PieChart>
  )
})

const StyledText = styled('text')(({ theme }) => ({
  ...theme.typography.h5,
  fill: theme.palette.text.primary,
  textAnchor: 'middle',
  dominantBaseline: 'central',
}))

const PieCenterLabel = React.memo(({ total, label }: { total: number; label: string }) => {
  const { width, height, left, top } = useDrawingArea()

  return (
    <StyledText x={left + width / 2} y={top + height / 2}>
      <tspan x={left + width / 2} dy="-0.4em">
        {total > 0 ? `${total.toLocaleString('ru')} ₽` : ''}
      </tspan>
      <tspan x={left + width / 2} dy="1.2em" style={{ fontSize: '0.7em' }}>
        {label}
      </tspan>
    </StyledText>
  )
})
