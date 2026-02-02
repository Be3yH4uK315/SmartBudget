import {
  getTransactions,
  setDateFrom,
  setDateTo,
  setType,
  setValueFrom,
  setValueTo,
} from '@features/transactions/store'
import { TransactionType } from '@features/transactions/types'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import dayjs from 'dayjs'

type TransactionsChip =
  | { type: 'category'; id: string }
  | { type: 'date'; from?: string; to?: string }
  | { type: 'value'; from?: number; to?: number }
  | { type: 'type'; value: string }

type Props = {
  localCategoryIds: string[]
  setLocalType: React.Dispatch<React.SetStateAction<'' | TransactionType>>
  setLocalValueFrom: React.Dispatch<React.SetStateAction<number | undefined>>
  setLocalValueTo: React.Dispatch<React.SetStateAction<number | undefined>>
  setLocalDateFrom: React.Dispatch<React.SetStateAction<string>>
  setLocalDateTo: React.Dispatch<React.SetStateAction<string>>
  localDateFrom: string
  localDateTo: string
  localValueFrom?: number
  localValueTo?: number
  localType: string
  handleRemoveCategoryId: (id: string) => void
}

export function useTransactionsChips({
  localCategoryIds,
  setLocalType,
  setLocalValueFrom,
  setLocalValueTo,
  setLocalDateFrom,
  setLocalDateTo,
  localDateFrom,
  localDateTo,
  localValueFrom,
  localValueTo,
  localType,
  handleRemoveCategoryId,
}: Props) {
  const translate = useTranslate('Transactions')
  const translateCategory = useTranslate('Categories')
  const dispatch = useAppDispatch()

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
          return translate('Filters.Value.range', { from: chip.from, to: chip.to })

        if (chip.from !== undefined) return translate('Filters.Value.from', { from: chip.from })

        if (chip.to !== undefined) return translate('Filters.Value.to', { to: chip.to })

        return ''
    }
  }

  const handleDeleteChip = (chip: TransactionsChip) => {
    switch (chip.type) {
      case 'category':
        handleRemoveCategoryId(chip.id)
        break

      case 'type':
        setLocalType('')
        dispatch(setType(''))
        dispatch(getTransactions())
        break

      case 'value':
        setLocalValueFrom(undefined)
        setLocalValueTo(undefined)
        dispatch(setValueFrom(undefined))
        dispatch(setValueTo(undefined))
        dispatch(getTransactions())
        break

      case 'date':
        setLocalDateFrom('')
        setLocalDateTo('')
        dispatch(setDateFrom(''))
        dispatch(setDateTo(''))
        dispatch(getTransactions())
        break
    }
  }

  return { chips, getLabel, handleDeleteChip }
}
