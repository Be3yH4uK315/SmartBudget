import { useEffect } from 'react'
import {
  getBudgetData,
  selectBudgetCategories,
  selectBudgetCurrentValue,
  selectBudgetTotalLimit,
  selectCategoriesWithLimits,
  selectIsAutoRenew,
  selectOverflowCategories,
} from '@features/budget/store'
import { Stack, Typography } from '@mui/material'
import {
  IconButton,
  PieChartWithCenterLabel,
  ScreenBackgroundBlock,
  StyledPaper,
  TransactionsPieBlock,
} from '@shared/components'
import { ScreenContent } from '@shared/components/ScreenContent'
import { MODAL_IDS } from '@shared/constants/modals'
import { ROUTES } from '@shared/constants/routes'
import { useTransactionFilters, useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { CenterLabel } from '@shared/types/components'
import { formatCurrency } from '@shared/utils/formatCurrency'
import { mapBudgetCategories, mapPlanedBudgetData } from '@shared/utils/transactionsBlockAdapters'
import { useNavigate } from 'react-router'
import { CategoriesBlock } from './CategoriesBlock/CategoriesBlock'
import { NoDataFallback } from './NoDataFallback'
import { OverflowCategoriesBlock } from './OverflowCategoriesBlock/OverflowCategoriesBlock'

export default function BudgetScreen() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const translate = useTranslate('Budget')

  const { limitedCount, limited, unlimited, incomeCategory } = useAppSelector(
    selectCategoriesWithLimits,
  )
  const { preOverflow, overflow } = useAppSelector(selectOverflowCategories)
  const currentValue = useAppSelector(selectBudgetCurrentValue)
  const categories = useAppSelector(selectBudgetCategories)
  const totalLimit = useAppSelector(selectBudgetTotalLimit)
  const isAutoRenew = useAppSelector(selectIsAutoRenew)

  const { normalizedData: factData } = useTransactionFilters(
    categories,
    mapBudgetCategories,
    'expense',
  )

  const { normalizedData: planedData, total: planedTotal } = useTransactionFilters(
    limited,
    mapPlanedBudgetData,
    'expense',
  )

  useEffect(() => {
    dispatch(getBudgetData())
  }, [])

  const handleRedirect = () => navigate(ROUTES.PAGES.BUDGET_SETTINGS)

  const settingsButtonTitle = translate('settingsButtonTitle')
  const settingsButtonSubtitle = translate('settingsButtonSubtitle')
  const planedTitle = translate(`PlanExpense.subtitle${totalLimit > 0 ? '' : 'ByCategories'}`)

  const factCenterLabel: CenterLabel = {
    type: 'amount',
    total: currentValue,
  }

  const planedCenterLabel: CenterLabel = {
    type: 'amount',
    total: totalLimit === 0 ? planedTotal : totalLimit,
  }
  return (
    <ScreenContent>
      <ScreenBackgroundBlock />
      <Stack spacing={2} sx={{ zIndex: 20, pt: 4 }}>
        <Typography variant="h3" pl={2}>
          {translate('title')}
        </Typography>

        <Stack direction={{ md: 'row' }} spacing={{ xs: 2, md: 2 }} width={'100%'}>
          <Stack spacing={2} width={{ xs: '100%', md: '50%' }}>
            <StyledPaper>
              <Typography variant="h4">
                {translate('CategoryBlock.category', { count: limitedCount })}
              </Typography>

              <Typography fontWeight={600}>{translate('CategoryBlock.title')}</Typography>

              <Typography variant="caption">{translate('CategoryBlock.subtitle')}</Typography>
            </StyledPaper>

            {overflow.length > 0 && (
              <OverflowCategoriesBlock variant="overflow" categories={overflow} />
            )}

            {preOverflow.length > 0 && (
              <OverflowCategoriesBlock variant="preOverflow" categories={preOverflow} />
            )}
          </Stack>

          <Stack spacing={2} width={'100%'}>
            <Stack
              direction={{ xs: 'column', md: 'row' }}
              spacing={{ xs: 2, md: 2 }}
              width={'100%'}
            >
              <Stack spacing={2}>
                <StyledPaper>
                  <Stack>
                    <Typography variant="h4">{translate('IsAutoRenew.title')}</Typography>

                    <Typography>
                      {isAutoRenew ? translate('IsAutoRenew.on') : translate('IsAutoRenew.off')}
                    </Typography>
                  </Stack>
                </StyledPaper>

                <StyledPaper>
                  <Stack>
                    <Typography variant="h5">{translate('income')}</Typography>

                    <Typography>{formatCurrency(incomeCategory.currentValue)}</Typography>
                  </Stack>
                </StyledPaper>
              </Stack>

              {planedData.length === 0 && (
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
                <StyledPaper paperSx={{ flex: 1, gap: 2 }}>
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
            </Stack>

            <TransactionsPieBlock
              title={translate('transactionsBlockTitle')}
              pieData={factData}
              centerLabel={factCenterLabel}
            />

            {limitedCount !== 0 && <CategoriesBlock categories={limited} />}

            <CategoriesBlock categories={unlimited} isLimited={false} />

            <IconButton
              // onClick={handleRedirect}
              onClick={() => dispatch(openModal({ id: MODAL_IDS.CREATE_BUDGET }))}
              title={settingsButtonTitle}
              subtitle={settingsButtonSubtitle}
            />
          </Stack>
        </Stack>
      </Stack>
    </ScreenContent>
  )
}
