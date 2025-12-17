import { createContext, PropsWithChildren, useCallback, useEffect, useMemo, useState } from 'react'
import { _localeManager } from '@shared/locale/localeManager'
import { Languages, OneLocaleDictionary } from '@shared/types/locale'

export const LocalizationContext = createContext<{
  language: Languages
  changeLanguage(newLanguage: Languages): Promise<void>
} | null>(null)

type Props = PropsWithChildren<{
  dictionaryLoader?(lang: Languages): Promise<OneLocaleDictionary | undefined>
}>

export const LocalizationProvider = ({ dictionaryLoader, children }: Props) => {
  const [language, setLanguage] = useState<Languages>(() => _localeManager.getLocale())

  const loadAndStoreDict = useCallback(
    async (lang: Languages = _localeManager.getLocale()) => {
      const externalDict = await dictionaryLoader?.(lang)
      await _localeManager.updateLocale(lang, externalDict)
    },
    [dictionaryLoader],
  )

  const changeLanguage = useCallback(
    async (lang: Languages) => {
      await loadAndStoreDict(lang)
      setLanguage(lang)
    },
    [loadAndStoreDict],
  )

  useEffect(() => {
    loadAndStoreDict()
  }, [loadAndStoreDict])

  return (
    <LocalizationContext.Provider
      value={useMemo(() => ({ language, changeLanguage }), [language, changeLanguage])}
    >
      {children}
    </LocalizationContext.Provider>
  )
}
