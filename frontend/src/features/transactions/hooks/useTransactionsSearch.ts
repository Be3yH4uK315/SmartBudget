import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { SEARCH_DEBOUNCE, SEARCH_LIMIT } from '@shared/constants'
import { ApiFunc } from '@shared/types/components'
import { debounce, showToast } from '@shared/utils'

export function useSearch<T>(apiFunc: ApiFunc<T>) {
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [results, setResults] = useState<T[]>([])
  const abortControllerRef = useRef<AbortController>(null)

  const search = useCallback(
    async (query: string) => {
      if (!query.trim()) {
        abortControllerRef.current?.abort()
        setResults([])
        setIsLoading(false)
        return
      }

      abortControllerRef.current?.abort()
      const controller = new AbortController()
      abortControllerRef.current = controller

      setIsLoading(true)

      try {
        const response = await apiFunc(query, controller.signal, SEARCH_LIMIT)

        if (controller.signal.aborted) return

        setResults(response)
      } catch (e: any) {
        if (e.name !== 'AbortError') {
          showToast({ messageKey: 'cannotSearch', type: 'error' })
        }
      } finally {
        setIsLoading(false)
      }
    },
    [apiFunc],
  )

  const clearResults = useCallback(() => {
    abortControllerRef.current?.abort()
    setResults([])
    setIsLoading(false)
  }, [])

  const debouncedSearch = useMemo(() => debounce(search, SEARCH_DEBOUNCE), [search])

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort()
      debouncedSearch.cancel()
    }
  }, [debouncedSearch])

  return { results, isLoading, debouncedSearch, clearResults }
}
