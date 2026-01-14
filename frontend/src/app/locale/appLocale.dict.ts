import { budgetDict } from '@features/budget/locale'
import { dashboardDict } from '@features/dashboard/locale'
import { settingsDict } from '@features/settings/locale'
import { transactionsDict } from '@features/transactions/locale'
import { authDict, categoriesDict, monthDict, sharedDict, toastsDict } from '@shared/locale/dicts'
import { mergeLocaleDicts } from '@shared/utils/locale.helpers'
import { goalsDict } from 'src/features/goals/locale/goals.dict'

export const appLocaleDict = mergeLocaleDicts(
  authDict,
  budgetDict,
  categoriesDict,
  dashboardDict,
  goalsDict,
  monthDict,
  toastsDict,
  transactionsDict,
  settingsDict,
  sharedDict,
)
