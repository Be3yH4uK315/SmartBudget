import { Notification } from '@features/notifications/types'
import { CATEGORY_IDS } from '@shared/constants'
import { ROUTES } from '@shared/constants/routes'
import { formatCurrency, formatPercent } from '@shared/utils'

type TranslateFunc = (key: string, params?: Record<string, any>) => string

export const mapNotificationMessage = (
  notification: Notification,
  translate: TranslateFunc,
  translateCategories: TranslateFunc,
): string => {
  switch (notification.messageKey) {
    case 'Limit.preOverflow.message':
    case 'Limit.overflow.message': {
      const { categoryId } = notification.props as { categoryId: number }

      return translate(notification.messageKey, {
        value: translateCategories(String(categoryId)),
      })
    }

    case 'Transactions.categoryChanged.message': {
      const { oldCategory, newCategory } = notification.props as {
        oldCategory: number
        newCategory: number
      }

      return translate(notification.messageKey, {
        oldCategory: translateCategories(String(oldCategory)),
        newCategory: translateCategories(String(newCategory)),
      })
    }

    case 'Transactions.unclassified.message': {
      const { value } = notification.props as { value: number }

      return translate(notification.messageKey, {
        count: value,
      })
    }

    case 'Budget.preOverflow.message': {
      const { value } = notification.props as { value: number }

      return translate(notification.messageKey, {
        value: formatCurrency(value),
      })
    }

    case 'Goals.deadlineIsComing.message': {
      const { currentPercent, daysLeft, ...rest } = notification.props as {
        goalId: string
        name: string
        daysLeft: number
        currentPercent: number
      }

      return translate(notification.messageKey, {
        ...rest,
        count: daysLeft,
        currentPercent: formatPercent(currentPercent),
      })
    }

    case 'Goals.goalCreated.message': {
      const { recommendedPayment, ...rest } = notification.props as {
        goalId: string
        name: string
        recommendedPayment: number
      }

      return translate(notification.messageKey, {
        ...rest,
        recommendedPayment: formatCurrency(recommendedPayment),
      })
    }

    default:
      return translate(notification.messageKey, {
        ...notification.props,
      })
  }
}

export const getNotificationOnClickLink = (notification: Notification) => {
  if (notification.link) return notification.link

  switch (notification.service) {
    case 'Goals': {
      const { goalId } = notification.props as { goalId: string }

      return `${ROUTES.PAGES.GOALS.MAIN}/${goalId}`
    }

    case 'Transactions': {
      if (notification.messageKey === 'Transactions.unclassified.message')
        return `${ROUTES.PAGES.TRANSACTIONS}/?categoriesIds=${CATEGORY_IDS[30]}`

      return undefined
    }
    case 'Limit':
      return ROUTES.PAGES.BUDGET

    case 'Security':
      return ROUTES.PAGES.SETTINGS.SECURITY

    case 'Budget':
      return ROUTES.PAGES.BUDGET
  }
}

export function isTransactionCategoryChanged(
  n: Notification,
): n is Notification<'Transactions.categoryChanged.message'> {
  return n.messageKey === 'Transactions.categoryChanged.message'
}
