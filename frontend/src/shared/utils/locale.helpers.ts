import { appLocaleDict } from '@app/locale'
import { Languages, LocaleDictionary, UnionToIntersection } from '@shared/types'

export function getInitialLanguage(fallback: Languages = 'ru'): Languages {
  const stored = localStorage.getItem('language') as Languages | null
  if (stored && appLocaleDict[stored]) return stored

  const nav = navigator.language?.slice(0, 2).toLowerCase() as Languages
  if (nav && appLocaleDict[nav]) return nav

  return fallback
}

export function mergeLocaleDicts<T extends LocaleDictionary[]>(
  ...dicts: T
): UnionToIntersection<T[number]> {
  return dicts.reduce(
    (merged, dict) => ({
      ru: { ...merged.ru, ...dict.ru },
      en: { ...merged.en, ...dict.en },
    }),
    dicts[0],
  ) as any
}
