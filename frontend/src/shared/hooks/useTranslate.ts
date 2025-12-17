import { useCallback, useContext } from 'react'
import { LocalizationContext } from '@app/providers'
import { _localeManager } from '@shared/locale/localeManager'
import { LocaleDictionary } from '@shared/types'

export function useTranslate<BlockName extends keyof LocaleDictionary['ru']>(block: BlockName) {
  useLocalization()

  return useCallback(
    (blockKey: keyof LocaleDictionary['ru'][BlockName], params?: Record<string, unknown>) => {
      const fullKey = `${String(block)}.${String(blockKey)}`
      return _localeManager.translate(fullKey, params)
    },
    [block],
  )
}

function useLocalization() {
  const ctx = useContext(LocalizationContext)
  if (!ctx) {
    throw new Error('useLocalization must be used within <LocalizationProvider />')
  }
  return ctx
}
