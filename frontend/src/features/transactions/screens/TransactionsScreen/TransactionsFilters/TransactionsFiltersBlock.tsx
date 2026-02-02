import { useTransactionsChips, useTransactionsFilters } from '@features/transactions/hooks'
import { TransactionsFilters, TransactionType } from '@features/transactions/types'
import { Button, Chip, Grid, Stack } from '@mui/material'
import { FiltersSelect, StyledBox } from '@shared/components'
import { CATEGORY_IDS } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { TransactionsRangePopover } from './TransactionsRangePopover'

type Props = {
  filters: TransactionsFilters
}

export const TransactionsFiltersBlock = ({ filters }: Props) => {
  const translate = useTranslate('Transactions')

  const {
    dirty,
    localCategoryIds,
    localType,
    localDateFrom,
    localDateTo,
    localValueFrom,
    localValueTo,
    setLocalType,
    setLocalValueFrom,
    setLocalValueTo,
    setLocalDateFrom,
    setLocalDateTo,
    handleCategoryIdsChange,
    handleTypeChange,
    handleDateFromChange,
    handleDateToChange,
    handleValueFromChange,
    handleValueToChange,
    handleApplyCategories,
    handleApplyDates,
    handleApplyValues,
    handleClearFilters,
    handleRemoveCategoryId,
  } = useTransactionsFilters(filters)

  const { chips, getLabel, handleDeleteChip } = useTransactionsChips({
    localCategoryIds,
    localType,
    localDateFrom,
    localDateTo,
    localValueFrom,
    localValueTo,
    handleRemoveCategoryId,
    setLocalType,
    setLocalValueFrom,
    setLocalValueTo,
    setLocalDateFrom,
    setLocalDateTo,
  })

  return (
    <Stack spacing={2}>
      <Grid container spacing={2} alignItems="center">
        <Grid size={{ xs: 6, sm: 'auto' }}>
          <FiltersSelect<string>
            multiple
            value={localCategoryIds}
            items={CATEGORY_IDS.map(String)}
            translateItemKey={'Categories'}
            translateKey={'Transactions.Filters'}
            placeholderKey={'placeholder.categories'}
            onChange={handleCategoryIdsChange}
            onClose={handleApplyCategories}
            formSx={{ width: { xs: '100%', sm: 'auto' } }}
          />
        </Grid>

        <Grid size={{ xs: 6, sm: 'auto' }}>
          <FiltersSelect<TransactionType | ''>
            value={localType}
            items={['', 'income', 'expense']}
            translateItemKey={'Transactions.Filters.Type'}
            translateKey={'Transactions.Filters'}
            placeholderKey={'placeholder.type'}
            onChange={handleTypeChange}
            formSx={{ width: { xs: '100%', sm: 'auto' } }}
          />
        </Grid>

        <Grid size={'auto'}>
          <TransactionsRangePopover
            labelKey={'value'}
            from={localValueFrom}
            to={localValueTo}
            type="number"
            onChangeFrom={handleValueFromChange}
            onChangeTo={handleValueToChange}
            onClose={handleApplyValues}
          />
        </Grid>

        <Grid size={'auto'}>
          <TransactionsRangePopover
            labelKey={'date'}
            from={localDateFrom}
            to={localDateTo}
            type="date"
            onChangeFrom={handleDateFromChange}
            onChangeTo={handleDateToChange}
            onClose={handleApplyDates}
          />
        </Grid>

        {dirty && (
          <Grid size={{ xs: 12, sm: 'auto' }}>
            <Button
              onClick={handleClearFilters}
              sx={{ height: 'min-content', width: { xs: '100%', sm: 'auto' } }}
              variant="yellow"
            >
              {translate('Filters.clear')}
            </Button>
          </Grid>
        )}
      </Grid>

      {dirty && (
        <StyledBox>
          {chips.map((chip, i) => (
            <Chip
              key={i}
              label={getLabel(chip)}
              onDelete={() => handleDeleteChip(chip)}
              sx={{
                bgcolor: 'primary.main',
                color: '#333',
                typography: 'caption',
                '& .MuiSvgIcon-root': { color: '#333' },
              }}
            />
          ))}
        </StyledBox>
      )}
    </Stack>
  )
}
