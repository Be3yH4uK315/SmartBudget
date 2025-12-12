export type Languages = 'ru' | 'en'

export type OneLocaleDictionary = Record<string, any>

export type LocaleDictionary = Record<Languages, OneLocaleDictionary>

/**
 * Взято отсюда https://stackoverflow.com/questions/50374908/transform-union-type-to-intersection-type/50375286#50375286
 */
export type UnionToIntersection<U> = (U extends any ? (k: U) => void : never) extends (
  k: infer I,
) => void
  ? I
  : never

export type LocaleNamespace = keyof LocaleDictionary['ru']
