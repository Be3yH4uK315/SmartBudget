import { useEffect } from 'react'
import { CategoriesBlock, InfoBlock, OverflowCategoriesBlock } from '@features/budget/components'
import { useBudgetData, useBudgetPieData } from '@features/budget/hooks'
import {
  clearBudgetState,
  getBudgetData,
  selectBudgetCategories,
  selectBudgetTotalIncome,
  selectBudgetTotalLimit,
  selectIsAutoRenew,
  selectIsBudgetLoading,
} from '@features/budget/store'
import { Stack, Typography } from '@mui/material'
import {
  IconButton,
  ScreenBackgroundBlock,
  ScreenContent,
  StyledPaper,
  TransactionsPieBlock,
} from '@shared/components'
import { ROUTES } from '@shared/constants/routes'
import { useTransactionFilters, useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { formatCurrency, mapBudgetCategories, mapPlanedBudgetData } from '@shared/utils'
import { useNavigate } from 'react-router'
import { BudgetScreenSkeleton } from './BudgetScreenSkeleton'
import { PlannedBudgetBlock } from './PlannedBudgetBlock'

export default function BudgetScreen() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const translate = useTranslate('Budget')

  const categories = useAppSelector(selectBudgetCategories)
  const totalLimit = useAppSelector(selectBudgetTotalLimit)
  const isAutoRenew = useAppSelector(selectIsAutoRenew)
  const isLoading = useAppSelector(selectIsBudgetLoading)
  const totalIncome = useAppSelector(selectBudgetTotalIncome)

  const { limited, unlimited, limitedSum, preOverflow, overflow } = useBudgetData({
    categories,
  })

  const {
    normalizedData: factData,
    activeType,
    toggleFilter,
    total: factTotal,
  } = useTransactionFilters(categories, mapBudgetCategories, 'expense')

  const { normalizedData: rawPlanedData, total: planedTotal } = useTransactionFilters(
    limited,
    mapPlanedBudgetData,
    'expense',
  )

  const { planedData, factCenterLabel, planedCenterLabel } = useBudgetPieData({
    totalLimit,
    rawPlanedData,
    limitedSum,
    currentValue: factTotal,
    planedTotal,
  })

  useEffect(() => {
    dispatch(getBudgetData())
  }, [dispatch])

  useEffect(() => {
    return () => {
      dispatch(clearBudgetState())
    }
  }, [dispatch])

  const handleRedirect = () => navigate(ROUTES.PAGES.SETTINGS.BUDGET)

  const settingsButtonTitle = translate('settingsButtonTitle')
  const settingsButtonSubtitle = translate('settingsButtonSubtitle')

  return (
    <ScreenContent isLoading={isLoading} ContentSkeleton={BudgetScreenSkeleton}>
      <ScreenBackgroundBlock />
      <Stack spacing={2} sx={{ zIndex: 20, pt: 4 }}>
        <Typography variant="h3" pl={2} color="#333333">
          {translate('title')}
        </Typography>

        <Stack direction={{ md: 'row' }} spacing={{ xs: 2, md: 2 }} width={'100%'}>
          <Stack spacing={2} width={{ xs: '100%', md: '50%' }}>
            <StyledPaper>
              <Typography variant="h4">
                {translate('CategoryInfoBlock.category', { count: limited.length })}
              </Typography>

              <Typography fontWeight={600}>{translate('CategoryInfoBlock.title')}</Typography>

              <Typography variant="caption">{translate('CategoryInfoBlock.subtitle')}</Typography>
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
                <InfoBlock
                  title={translate('IsAutoRenew.title')}
                  subtitle={
                    isAutoRenew ? translate('IsAutoRenew.on') : translate('IsAutoRenew.off')
                  }
                />

                <InfoBlock title={translate('income')} subtitle={formatCurrency(totalIncome)} />

                <IconButton
                  onClick={handleRedirect}
                  title={settingsButtonTitle}
                  subtitle={settingsButtonSubtitle}
                  paperSx={{ flex: '1 0 0%' }}
                />
              </Stack>

              <PlannedBudgetBlock
                totalLimit={totalLimit}
                rawPlanedData={rawPlanedData}
                planedData={planedData}
                planedCenterLabel={planedCenterLabel}
              />
            </Stack>

            <TransactionsPieBlock
              activeType={activeType}
              toggleFilter={toggleFilter}
              title={translate('transactionsBlockTitle')}
              pieData={factData}
              centerLabel={factCenterLabel}
            />

            {limited.length !== 0 && <CategoriesBlock categories={limited} />}

            {unlimited.length !== 0 && <CategoriesBlock categories={unlimited} isLimited={false} />}
          </Stack>
        </Stack>
      </Stack>
    </ScreenContent>
  )
}
