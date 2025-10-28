import { createContext, PropsWithChildren, useCallback, useLayoutEffect, useState } from 'react'
import { _localeManager } from '@shared/locale/localeManager'

export const LocalizationContext = createContext<{
  language: Languages
  changeLanguage(newLanguage: Languages): Promise<void>
} | null>(null)

type Props = PropsWithChildren<{
  dictionaryLoader?(lang: Languages): Promise<OneLocaleDictionary | undefined>
}>

export const LocalizationProvider = ({ dictionaryLoader, children }: Props) => {
  const [language, setLanguage] = useState<Languages>(_localeManager.getLocale())

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

  useLayoutEffect(() => {
    loadAndStoreDict()
  }, [loadAndStoreDict])

  return (
    <LocalizationContext.Provider
      value={{
        language,
        changeLanguage,
      }}
    >
      {children}
    </LocalizationContext.Provider>
  )
}
