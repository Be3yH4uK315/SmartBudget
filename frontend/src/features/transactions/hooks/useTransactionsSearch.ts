import { useEffect, useState } from 'react'
import { transactionsApi, transactionsMock } from '@features/transactions/api'
import { SEARCH_DEBOUNCE, SEARCH_LIMIT } from '@features/transactions/constants'
import { Transaction } from '@features/transactions/types'
import { showToast } from '@shared/utils'

export function useTransactionsSearch() {
  const [inputValue, setInputValue] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [options, setOptions] = useState<Transaction[]>([])

  useEffect(() => {
    if (!inputValue.trim()) {
      setOptions([])
      return
    }

    const controller = new AbortController()

    setOptions([])
    setIsLoading(true)

    const searchOptions = async () => {
      try {
        const response = await transactionsMock.searchTransactions(
          inputValue,
          SEARCH_LIMIT,
          controller.signal,
        )
        setOptions(response)
      } catch (e: any) {
        if (e.name !== 'AbortError') {
          showToast({ messageKey: 'cannotSearchTransactions', type: 'error' })
        }
      } finally {
        setIsLoading(false)
      }
    }

    const id = setTimeout(searchOptions, SEARCH_DEBOUNCE)

    return () => {
      clearTimeout(id)
      controller.abort()
    }
  }, [inputValue])

  return { options, isLoading, inputValue, setInputValue }
}
