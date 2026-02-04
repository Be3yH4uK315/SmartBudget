import { useTransactionsChips } from '@features/transactions/hooks'
import { TransactionsFilters, TransactionType } from '@features/transactions/types'
import { Button, Chip, Grid, SelectChangeEvent, Stack } from '@mui/material'
import { FiltersSelect, StyledBox } from '@shared/components'
import { CATEGORY_IDS } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { TransactionsRangePopover } from './TransactionsRangePopover'

type Props = {
  isDirty: boolean
  localCategoryIds: string[]
  localType: TransactionType | ''
  localDateFrom: string
  localDateTo: string
  localValueFrom: number | undefined
  localValueTo: number | undefined
  appliedFiltersRef: React.RefObject<TransactionsFilters>
  setLocalType: React.Dispatch<React.SetStateAction<'' | TransactionType>>
  setLocalValueFrom: React.Dispatch<React.SetStateAction<number | undefined>>
  setLocalValueTo: React.Dispatch<React.SetStateAction<number | undefined>>
  setLocalDateFrom: React.Dispatch<React.SetStateAction<string>>
  setLocalDateTo: React.Dispatch<React.SetStateAction<string>>
  handleCategoryIdsChange: (e: SelectChangeEvent<string[]>) => void
  handleTypeChange: (e: SelectChangeEvent<string>) => void
  handleDateFromChange: (value: string) => void
  handleDateToChange: (value: string) => void
  handleValueFromChange: (value?: number | undefined) => void
  handleValueToChange: (value?: number | undefined) => void
  handleApplyCategories: (next?: string[]) => void
  handleApplyType: (newType?: '' | TransactionType) => void
  handleApplyDates: (from?: string, to?: string) => void
  handleApplyValues: (from?: number, to?: number) => void
  handleClearFilters: () => void
  handleRemoveCategoryId: (value: number) => void
}

export const TransactionsFiltersBlock = ({ ...props }: Props) => {
  const translate = useTranslate('Transactions')

  const {
    isDirty,
    localCategoryIds,
    localType,
    localDateFrom,
    localDateTo,
    localValueFrom,
    localValueTo,
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
  } = props

  const { chips, getLabel, handleDeleteChip } = useTransactionsChips({ ...props })

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

        {isDirty && (
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

      {isDirty && (
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
