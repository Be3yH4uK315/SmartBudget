import { useMemo } from 'react'
import { useTheme } from '@mui/material'
import { CenterLabel, PieDataItem } from '@shared/types/components'

type Props = {
  totalLimit: number
  rawPlanedData: PieDataItem[]
  limitedSum: number
  currentValue: number
  planedTotal: number
}

export const useBudgetPieData = ({
  totalLimit,
  rawPlanedData,
  limitedSum,
  currentValue,
  planedTotal,
}: Props) => {
  const theme = useTheme()
  const color = theme.palette.grayButton.dark

  const { planedData, factCenterLabel, planedCenterLabel } = useMemo(() => {
    const planedData: PieDataItem[] =
      totalLimit !== 0
        ? [
            ...rawPlanedData,
            {
              value: totalLimit - limitedSum,
              label: '32',
              color: color,
            },
          ]
        : rawPlanedData

    const factCenterLabel: CenterLabel = {
      type: 'amount',
      total: currentValue,
    }

    const planedCenterLabel: CenterLabel = {
      type: 'amount',
      total: totalLimit === 0 ? planedTotal : totalLimit,
    }

    return { planedData, factCenterLabel, planedCenterLabel }
  }, [currentValue, limitedSum, planedTotal, rawPlanedData, color, totalLimit])

  return { planedData, factCenterLabel, planedCenterLabel }
}
