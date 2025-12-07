import { dashboardDict } from '@features/dashboard/locale'
import { authDict, categoriesDict, errorsDict, sharedDict } from '@shared/locale/dicts'
import { mergeLocaleDicts } from '@shared/utils'

export const appLocaleDict = mergeLocaleDicts(
  authDict,
  categoriesDict,
  dashboardDict,
  errorsDict,
  sharedDict,
)
