import { TransactionsFilters, TransactionType } from '@features/transactions/types'
import { useTranslate } from '@shared/hooks'
import { formatCurrency } from '@shared/utils/formatCurrency'
import dayjs from 'dayjs'

type TransactionsChip =
  | { type: 'category'; id: string }
  | { type: 'date'; from?: string; to?: string }
  | { type: 'value'; from?: number; to?: number }
  | { type: 'type'; value: string }

type Props = {
  appliedFiltersRef: React.RefObject<TransactionsFilters>
  localCategoryIds: string[]
  localDateFrom: string
  localDateTo: string
  localValueFrom?: number
  localValueTo?: number
  localType: string
  setLocalType: React.Dispatch<React.SetStateAction<'' | TransactionType>>
  setLocalValueFrom: React.Dispatch<React.SetStateAction<number | undefined>>
  setLocalValueTo: React.Dispatch<React.SetStateAction<number | undefined>>
  setLocalDateFrom: React.Dispatch<React.SetStateAction<string>>
  setLocalDateTo: React.Dispatch<React.SetStateAction<string>>
  handleApplyCategories: (value?: string[]) => void
  handleApplyType: (value?: '' | TransactionType) => void
  handleApplyDates: (from?: string, to?: string) => void
  handleApplyValues: (from?: number, to?: number) => void
  handleRemoveCategoryId: (value: number) => void
}

export function useTransactionsChips({
  localCategoryIds,
  localDateFrom,
  localDateTo,
  localValueFrom,
  localValueTo,
  localType,
  setLocalType,
  setLocalValueFrom,
  setLocalValueTo,
  setLocalDateFrom,
  setLocalDateTo,
  handleApplyType,
  handleApplyDates,
  handleApplyValues,
  handleRemoveCategoryId,
}: Props) {
  const translate = useTranslate('Transactions')
  const translateCategory = useTranslate('Categories')

  const chips: TransactionsChip[] = []

  localCategoryIds.forEach((id) => chips.push({ type: 'category', id }))

  if (localDateFrom || localDateTo) {
    chips.push({
      type: 'date',
      from: localDateFrom ? dayjs(localDateFrom).format('DD.MM.YYYY') : undefined,
      to: localDateTo ? dayjs(localDateTo).format('DD.MM.YYYY') : undefined,
    })
  }

  if (localValueFrom !== undefined || localValueTo !== undefined)
    chips.push({ type: 'value', from: localValueFrom, to: localValueTo })

  if (localType) chips.push({ type: 'type', value: localType })

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
      case 'category':
        handleRemoveCategoryId(Number(chip.id))
        break

      case 'type': {
        handleApplyType('')
        setLocalType('')
        break
      }

      case 'value': {
        handleApplyValues(-1, -1)
        setLocalValueFrom(undefined)
        setLocalValueTo(undefined)
        break
      }

      case 'date': {
        handleApplyDates('', '')
        setLocalDateFrom('')
        setLocalDateTo('')
        break
      }
    }
  }

  return { chips, getLabel, handleDeleteChip }
}
