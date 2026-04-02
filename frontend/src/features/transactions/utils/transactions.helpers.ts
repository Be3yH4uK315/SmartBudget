import { Category } from '@features/transactions/types'
import { CATEGORY_IDS } from '@shared/constants'

export function parseCategoryIds(ids: string[]): Category[] {
  return ids.map(Number).filter((n): n is Category => CATEGORY_IDS.includes(n as Category))
}
