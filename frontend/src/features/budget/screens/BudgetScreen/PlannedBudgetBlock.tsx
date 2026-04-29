import { NoDataFallback } from '@features/budget/components'
import { Stack, Typography } from '@mui/material'
import { PieChartWithCenterLabel, StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { CenterLabel, PieDataItem } from '@shared/types/components'

type Props = {
  totalLimit: number
  rawPlanedData: PieDataItem[]
  planedData: PieDataItem[]
  planedCenterLabel: CenterLabel
}

export const PlannedBudgetBlock = ({
  totalLimit,
  rawPlanedData,
  planedData,
  planedCenterLabel,
}: Props) => {
  const translate = useTranslate('Budget')

  const planedTitle = translate(`PlanExpense.subtitle${totalLimit > 0 ? '' : 'ByCategories'}`)

  return (
    <>
      {totalLimit === 0 && rawPlanedData.length === 0 && (
        <StyledPaper
          paperSx={{
            flex: 1,
            height: '100%',
            p: 2,
          }}
        >
          <NoDataFallback />
        </StyledPaper>
      )}

      {planedData.length > 0 && (
        <StyledPaper paperSx={{ flex: 1, gap: 2, height: '100%' }}>
          <Stack>
            <Typography variant="h4">{translate('PlanExpense.title')}</Typography>

            <Typography>{planedTitle}</Typography>
          </Stack>

          <PieChartWithCenterLabel
            height={250}
            width={250}
            innerRadius={105}
            pieData={planedData}
            centerLabel={planedCenterLabel}
          />
        </StyledPaper>
      )}
    </>
  )
}
