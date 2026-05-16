import { CategoryNumber } from '@features/transactions/types'
import { CATEGORY_IDS } from '@shared/constants'

export function parseCategoryIds(ids: string[]): CategoryNumber[] {
  return ids
    .map(Number)
    .filter((n): n is CategoryNumber => CATEGORY_IDS.includes(n as CategoryNumber))
}
