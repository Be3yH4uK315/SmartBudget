import { useState } from 'react'
import { Add } from '@mui/icons-material'
import { Button, Checkbox, FormControlLabel, Grid, Stack, Typography } from '@mui/material'
import { EmptyList, NumberField, StyledPaper } from '@shared/components'
import { useBudgetForm, useTranslate } from '@shared/hooks'
import { formatPercent } from '@shared/utils'
import { AddCategoryCard, BudgetFormField, CategoryCard } from '.'

type Props = {
  values: ReturnType<typeof useBudgetForm>['values']
  availableCategories: number[]
  totalPercent: number
  remainingPercent: number
  isPercentOverflow: boolean
  setTotalLimit: (v: number) => void
  addCategory: (id: number) => void
  removeCategory: (id: number) => void
  updateAmount: (index: number, value: number) => void
  updatePercent: (index: number, value: number) => void
  toggleAutoRenew: (v: boolean) => void
}

export const BudgetForm = ({
  values,
  availableCategories,
  totalPercent,
  remainingPercent,
  isPercentOverflow,
  setTotalLimit,
  addCategory,
  removeCategory,
  updateAmount,
  updatePercent,
  toggleAutoRenew,
}: Props) => {
  const translate = useTranslate('BudgetForm')

  const [isAddingCategory, setIsAddingCategory] = useState(false)

  return (
    <Stack spacing={2} maxWidth={'800px'}>
      <BudgetFormField
        title={translate('BudgetLimit.title')}
        subtitle={translate('BudgetLimit.subtitle')}
        tooltip={translate('BudgetLimit.tooltip')}
      >
        <NumberField
          label={translate('BudgetLimit.valueLabel')}
          value={values.totalLimit ?? undefined}
          onChange={setTotalLimit}
        />
      </BudgetFormField>

      <BudgetFormField
        title={translate('AutoRenew.title')}
        tooltip={translate('AutoRenew.tooltip')}
        titleSpacing={0}
      >
        <FormControlLabel
          control={
            <Checkbox
              checked={values.isAutoRenew}
              onChange={(e) => toggleAutoRenew(e.target.checked)}
              sx={{ color: 'text.primary', '&.Mui-checked': { color: 'text.primary' } }}
            />
          }
          label={translate('AutoRenew.subtitle')}
        />
      </BudgetFormField>

      <BudgetFormField
        title={translate('CategoriesLimits.title')}
        tooltip={translate('CategoriesLimits.tooltip')}
        subtitle={
          values.totalLimit && values.categories.length
            ? translate('CategoriesLimits.remainingPercent', {
                value: formatPercent(remainingPercent / 100),
              })
            : undefined
        }
      >
        <Grid container spacing={1.5}>
          {!values.categories.length && !isAddingCategory ? (
            <Grid sx={{ height: '200px', width: '100%', display: 'flex' }}>
              <EmptyList
                reasonSubtitle={translate('EmptyList.subtitle')}
                reasonTitle={translate('EmptyList.title')}
              />
            </Grid>
          ) : (
            <>
              {values.categories.map((c, index) => (
                <CategoryCard
                  key={c.categoryId}
                  category={c}
                  onRemove={() => removeCategory(c.categoryId)}
                  onAmountChange={(v) => updateAmount(index, v)}
                  onPercentChange={(v) => updatePercent(index, v)}
                  totalLimit={values.totalLimit}
                />
              ))}

              {isAddingCategory && (
                <AddCategoryCard
                  categories={availableCategories}
                  onSelect={(id) => {
                    addCategory(id)
                    setIsAddingCategory(false)
                  }}
                  onCancel={() => setIsAddingCategory(false)}
                />
              )}
            </>
          )}
        </Grid>

        {!isAddingCategory && availableCategories.length > 0 && (
          <Button startIcon={<Add />} onClick={() => setIsAddingCategory(true)}>
            {translate('CategoriesLimits.AddCategoryCard.addCategoryButton')}
          </Button>
        )}
      </BudgetFormField>

      {!!values.totalLimit && isPercentOverflow && (
        <StyledPaper
          elevation={0}
          paperSx={{ border: '2px solid', borderColor: 'error.main', textAlign: 'center' }}
        >
          <Typography variant="h6">
            {translate('CategoriesLimits.percentOverflow', {
              value: formatPercent((totalPercent - 100) / 100),
            })}
          </Typography>
        </StyledPaper>
      )}
    </Stack>
  )
}
