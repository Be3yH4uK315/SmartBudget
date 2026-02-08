import { useTransactionsChips } from '@features/transactions/hooks'
import { TransactionsFilters, TransactionType } from '@features/transactions/types'
import { Button, Chip, Grid, Stack } from '@mui/material'
import { FiltersSelect, StyledBox } from '@shared/components'
import { CATEGORY_IDS } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import { TransactionsRangePopover } from './TransactionsRangePopover'

type Props = {
  isDirty: boolean
  localFilters: TransactionsFilters
  appliedFiltersRef: React.RefObject<TransactionsFilters>
  setLocalFilters: React.Dispatch<React.SetStateAction<TransactionsFilters>>
  applyFilters: (value: TransactionsFilters) => void
  handleClearFilters: () => void
  handleApply: () => void
  updateLocalFilters: <K extends keyof TransactionsFilters>(
    key: K,
    value: TransactionsFilters[K],
  ) => void
}

export const TransactionsFiltersBlock = ({ ...props }: Props) => {
  const translate = useTranslate('Transactions')

  const {
    isDirty,
    localFilters,
    applyFilters,
    setLocalFilters,
    handleApply,
    updateLocalFilters,
    handleClearFilters,
  } = props

  const { chips, getLabel, handleDeleteChip } = useTransactionsChips(props)

  return (
    <Stack spacing={2}>
      <Grid container spacing={2} alignItems="center">
        <Grid size={{ xs: 6, sm: 'auto' }}>
          <FiltersSelect<string>
            multiple
            value={localFilters.categoryIds.map(String)}
            items={CATEGORY_IDS.map(String)}
            translateItemKey={'Categories'}
            translateKey={'Transactions.Filters'}
            placeholderKey={'placeholder.categories'}
            onChange={(e) => updateLocalFilters('categoryIds', e.target.value)}
            onClose={handleApply}
            formSx={{ width: { xs: '100%', sm: 'auto' } }}
          />
        </Grid>

        <Grid size={{ xs: 6, sm: 'auto' }}>
          <FiltersSelect<TransactionType | ''>
            value={localFilters.type}
            items={['', 'income', 'expense']}
            translateItemKey={'Transactions.Filters.Type'}
            translateKey={'Transactions.Filters'}
            placeholderKey={'placeholder.type'}
            onChange={(e) => {
              const next = { ...localFilters, type: e.target.value }
              setLocalFilters(next)
              applyFilters(next)
            }}
            formSx={{ width: { xs: '100%', sm: 'auto' } }}
          />
        </Grid>

        <Grid size={'auto'}>
          <TransactionsRangePopover
            labelKey={'value'}
            from={localFilters.valueFrom}
            to={localFilters.valueTo}
            type="number"
            onChangeFrom={(e) => updateLocalFilters('valueFrom', e)}
            onChangeTo={(e) => updateLocalFilters('valueTo', e)}
            onClose={handleApply}
          />
        </Grid>

        <Grid size={'auto'}>
          <TransactionsRangePopover
            labelKey={'date'}
            from={localFilters.dateFrom}
            to={localFilters.dateTo}
            type="date"
            onChangeFrom={(e) => updateLocalFilters('dateFrom', e)}
            onChangeTo={(e) => updateLocalFilters('dateTo', e)}
            onClose={handleApply}
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
