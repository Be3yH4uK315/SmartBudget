import { dashboardDict } from '@features/dashboard/locale'
import { authDict, categoriesDict, sharedDict, toastsDict } from '@shared/locale/dicts'
import { mergeLocaleDicts } from '@shared/utils/locale.helpers'

export const appLocaleDict = mergeLocaleDicts(
  authDict,
  categoriesDict,
  dashboardDict,
  toastsDict,
  sharedDict,
)
