import { TransactionsChip, TransactionsFilters } from '@features/transactions/types'
import { useTranslate } from '@shared/hooks'
import { formatCurrency } from '@shared/utils/formatCurrency'
import dayjs from 'dayjs'

type Props = {
  localFilters: TransactionsFilters
  applyFilters: (value: TransactionsFilters) => void
  updateLocalFilters: <K extends keyof TransactionsFilters>(
    key: K,
    value: TransactionsFilters[K],
  ) => void
}

export function useTransactionsChips({ localFilters, updateLocalFilters, applyFilters }: Props) {
  const translate = useTranslate('Transactions')
  const translateCategory = useTranslate('Categories')

  const chips: TransactionsChip[] = []

  localFilters.categoryIds.forEach((id) => chips.push({ type: 'category', id }))

  if (localFilters.dateFrom || localFilters.dateTo) {
    chips.push({
      type: 'date',
      from: localFilters.dateFrom ? dayjs(localFilters.dateFrom).format('DD.MM.YYYY') : undefined,
      to: localFilters.dateTo ? dayjs(localFilters.dateTo).format('DD.MM.YYYY') : undefined,
    })
  }

  if (localFilters.valueFrom !== undefined || localFilters.valueTo !== undefined)
    chips.push({ type: 'value', from: localFilters.valueFrom, to: localFilters.valueTo })

  if (localFilters.type) chips.push({ type: 'type', value: localFilters.type })

  const getLabel = (chip: TransactionsChip) => {
    switch (chip.type) {
      case 'category':
        return translateCategory(`${chip.id}`)

      case 'type':
        return translate(`Filters.Type.${chip.value}`)

      case 'date':
        if (chip.from && chip.to)
          return translate('Filters.Date.range', { from: chip.from, to: chip.to })

        if (chip.from) return translate('Filters.Date.from', { from: chip.from })

        if (chip.to) return translate('Filters.Date.to', { to: chip.to })
        return ''

      case 'value':
        if (chip.from !== undefined && chip.to !== undefined)
          return translate('Filters.Value.range', {
            from: formatCurrency(chip.from),
            to: formatCurrency(chip.to),
          })

        if (chip.from !== undefined)
          return translate('Filters.Value.from', { from: formatCurrency(chip.from) })

        if (chip.to !== undefined)
          return translate('Filters.Value.to', { to: formatCurrency(chip.to) })

        return ''
    }
  }

  const handleDeleteChip = (chip: TransactionsChip) => {
    switch (chip.type) {
      case 'category': {
        const next = {
          ...localFilters,
          categoryIds: localFilters.categoryIds.filter((id) => id !== chip.id),
        }
        updateLocalFilters('categoryIds', next.categoryIds)
        applyFilters(next)
        break
      }

      case 'type': {
        const next = {
          ...localFilters,
          type: '' as const,
        }
        updateLocalFilters('type', next.type)
        applyFilters(next)
        break
      }

      case 'value': {
        const next = {
          ...localFilters,
          valueFrom: undefined,
          valueTo: undefined,
        }
        updateLocalFilters('valueFrom', next.valueFrom)
        updateLocalFilters('valueTo', next.valueTo)
        applyFilters(next)
        break
      }

      case 'date': {
        const next = {
          ...localFilters,
          dateFrom: '',
          dateTo: '',
        }
        updateLocalFilters('dateFrom', next.dateFrom)
        updateLocalFilters('dateTo', next.dateTo)
        applyFilters(next)
        break
      }
    }
  }

  return { chips, getLabel, handleDeleteChip }
}
