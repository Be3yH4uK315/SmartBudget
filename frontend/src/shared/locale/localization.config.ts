import i18next, { i18n } from 'i18next'
import { getInitialLanguage } from '@shared/utils/locale.helpers'
import { rootDictionary } from './rootDictionary'

let _instance: i18n | null = null

export function initI18n(): i18n {
  if (_instance) return _instance

  const initialLng = getInitialLanguage('ru')

  i18next.init({
    lng: initialLng,
    fallbackLng: 'ru',
    resources: Object.fromEntries(
      Object.entries(rootDictionary).map(([lng, dict]) => [lng, { translation: dict }]),
    ) as any,

    interpolation: {
      escapeValue: false,
    },

    returnNull: false,
    returnEmptyString: false,
    parseMissingKeyHandler(key) {
      return key
    },
  })

  _instance = i18next
  return i18next
}
