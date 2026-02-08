import { useEffect, useRef, useState } from 'react'
import { clearTransactionsState, getTransactions } from '@features/transactions/store'
import { TransactionsFilters } from '@features/transactions/types'
import { isSameFilters, parseCategoryIds } from '@features/transactions/utils'
import { useAppDispatch } from '@shared/store'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router'

export function useTransactionsFilters() {
  const dispatch = useAppDispatch()

  const [searchParams, setSearchParams] = useSearchParams()

  function getInitFilters(searchParams: URLSearchParams): TransactionsFilters {
    const categoryParam = searchParams.get('categoriesIds')

    return {
      categoryIds: parseCategoryIds(categoryParam?.split(',') ?? []),
      valueFrom: undefined,
      valueTo: undefined,
      dateFrom: '',
      dateTo: '',
      type: '',
    }
  }

  const [localFilters, setLocalFilters] = useState<TransactionsFilters>(() =>
    getInitFilters(searchParams),
  )

  const appliedFiltersRef = useRef<TransactionsFilters>(getInitFilters(searchParams))

  function normalizeFilters(filters: TransactionsFilters): TransactionsFilters {
    let { valueFrom, valueTo, dateFrom, dateTo } = filters

    if (valueFrom !== undefined && valueTo !== undefined && valueFrom > valueTo) {
      ;[valueFrom, valueTo] = [valueTo, valueFrom]
    }

    if (dateFrom && dateTo && dayjs(dateFrom).isAfter(dayjs(dateTo))) {
      ;[dateFrom, dateTo] = [dateTo, dateFrom]
    }

    return {
      ...filters,
      valueFrom,
      valueTo,
      dateFrom,
      dateTo,
    }
  }

  const updateLocalFilters = <K extends keyof TransactionsFilters>(
    key: K,
    value: TransactionsFilters[K],
  ) => {
    setLocalFilters((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const handleApply = () => {
    const normalized = normalizeFilters(localFilters)

    applyFilters(normalized)
    setLocalFilters(normalized)
  }

  const applyFilters = (nextFilters: TransactionsFilters) => {
    if (isSameFilters(nextFilters, appliedFiltersRef.current)) return

    appliedFiltersRef.current = nextFilters

    dispatch(clearTransactionsState())
    dispatch(getTransactions(nextFilters))
  }

  const handleClearFilters = () => {
    const emptyFilters: TransactionsFilters = {
      categoryIds: [],
      type: '',
      dateFrom: '',
      dateTo: '',
      valueFrom: undefined,
      valueTo: undefined,
    }

    setLocalFilters(emptyFilters)
    applyFilters(emptyFilters)
  }

  const isDirty = () => {
    return !isSameFilters(appliedFiltersRef.current, {
      categoryIds: [],
      type: '',
      dateFrom: '',
      dateTo: '',
      valueFrom: undefined,
      valueTo: undefined,
    })
  }

  useEffect(() => {
    setSearchParams(
      (prev) => {
        const params = new URLSearchParams(prev)

        if (localFilters.categoryIds.length) {
          params.set('categoriesIds', localFilters.categoryIds.join(','))
        } else {
          params.delete('categoriesIds')
        }

        return params
      },
      { replace: true },
    )
  }, [localFilters.categoryIds, setSearchParams])

  useEffect(() => {
    dispatch(getTransactions(localFilters))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    isDirty,
    appliedFiltersRef,
    localFilters,
    setLocalFilters,
    applyFilters,
    handleApply,
    updateLocalFilters,
    handleClearFilters,
  }
}
