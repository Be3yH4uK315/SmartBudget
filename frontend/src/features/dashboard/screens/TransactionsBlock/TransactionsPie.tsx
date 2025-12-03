import { styled } from '@mui/material'
import { PieChart, useDrawingArea } from '@mui/x-charts'

type Props = {
  data: Omit<normalizedCategory, 'lightColor'>[]
  total: number
  innerRadius?: number
  width?: number
  height?: number
  label: string
}

export const PieChartWithCenterLabel = ({
  data,
  innerRadius = 60,
  total = 0,
  width,
  height,
  label,
}: Props) => {
  return (
    <>
      {data.length ? (
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
      ) : null}
    </>
  )
}

const StyledText = styled('text')(({ theme }) => ({
  ...theme.typography.h5,
  fill: theme.palette.text.primary,
  textAnchor: 'middle',
  dominantBaseline: 'central',
}))

const PieCenterLabel = ({ total, label }: { total: number; label: string }) => {
  const { width, height, left, top } = useDrawingArea()

  return (
    <StyledText x={left + width / 2} y={top + height / 2}>
      <tspan x="50%" dy="-0.4em">
        {total > 0 ? `${total.toLocaleString('ru')} ₽` : ''}
      </tspan>
      <tspan x="50%" dy="1.2em" style={{ fontSize: '0.7em' }}>
        {label}
      </tspan>
    </StyledText>
  )
}
