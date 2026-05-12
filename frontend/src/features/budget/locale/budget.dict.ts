import { LocaleDictionary } from '@shared/types'

export const budgetDict: LocaleDictionary = {
  ru: {
    Budget: {
      title: 'Бюджет',
      settingsButtonTitle: 'Настроить бюджет',
      settingsButtonSubtitle:
        'Установка и редактирование лимита на бюджет, управление лимитами категорий',

      transactionsBlockTitle: 'Текущие расходы',
      income: 'Доходы',

      cannotFindData: 'К сожалению, у нас что-то сломалось :(',
      tryAgain: 'Попробуйте обновить страницу или загляните позже - мы обязательно все починим',

      CategoryInfoBlock: {
        category: 'Лимиты не установлены',
        category_one: '{{count}} категория',
        category_few: '{{count}} категории',
        category_many: '{{count}} категорий',

        title: 'Количество категорий с установленным лимитом',
        subtitle: 'Пришлем пуш-уведомление, когда достигните лимита в 80 и 100 %',
      },

      FactExpense: {
        title: 'Фактические расходы',
        subtitle: 'На основе ваших операций',
      },

      PlanExpense: {
        title: 'Запланированные расходы',
        subtitle: 'На основе лимитов по категориям и лимита бюджета',
        subtitleByCategories: 'На основе лимитов по категориям',
      },

      IsAutoRenew: {
        title: 'Автопродление бюджета',
        on: 'Включено',
        off: 'Выключено',
      },

      Modal: {
        createTitle: 'Создание бюджета',
        submitButton: 'Создать бюджет',
      },
    },

    Overflow: {
      overflowTitle: 'Превышение лимита',
      overflowSubtitle_one: 'Вы превысили лимит в {{count}} категории:',
      overflowSubtitle_few: 'Вы превысили лимит в {{count}} категориях:',
      overflowSubtitle_many: 'Вы превысили лимит в {{count}} категориях:',

      preOverflowTitle: 'Превышение лимита',
      preOverflowSubtitle_one: 'Вы почти превысили лимит в {{count}} категории:',
      preOverflowSubtitle_few: 'Вы почти превысили лимит в {{count}} категориях:',
      preOverflowSubtitle_many: 'Вы почти превысили лимит в {{count}} категориях:',
    },

    CategoryLimitBlock: {
      limitedTitle: 'Лимиты по категориям',
      limitedSubtitle: 'Категории, на которые вы установили лимит',
      unlimitedTitle: 'Категории без лимитов',
      unlimitedSubtitle: 'Установите лимит, чтобы держать расходы под контролем',
    },
  },

  en: {
    Budget: {
      title: 'Budget',
      settingsButtonTitle: 'Manage Budget',
      settingsButtonSubtitle: 'Set and edit your budget limit, manage category limits',

      transactionsBlockTitle: 'Current Expenses',
      income: 'Income',

      cannotFindData: 'Unfortunately, something went wrong :(',
      tryAgain: 'Try refreshing the page or check back later – we’ll fix it!',

      CategoryInfoBlock: {
        category: 'No limits set',
        category_one: '{{count}} category',
        category_other: '{{count}} categories',

        title: 'Number of categories with set limits',
        subtitle: 'We’ll send a push notification when you reach 80% and 100% of the limit',
      },

      FactExpense: {
        title: 'Actual Expenses',
        subtitle: 'Based on your transactions',
      },

      PlanExpense: {
        title: 'Planned Expenses',
        subtitle: 'Based on category limits and overall budget limit',
        subtitleByCategories: 'Based on category limits',
      },

      IsAutoRenew: {
        title: 'Auto-renew Budget',
        on: 'Enabled',
        off: 'Disabled',
      },

      Modal: {
        createTitle: 'Create Budget',
        submitButton: 'Create Budget',
      },
    },

    Overflow: {
      overflowTitle: 'Over Budget',
      overflowSubtitle_one: 'You have exceeded the limit in {{count}} category:',
      overflowSubtitle_other: 'You have exceeded the limit in {{count}} categories:',

      preOverflowTitle: 'Near Budget Limit',
      preOverflowSubtitle_one: 'You are close to the limit in {{count}} category:',
      preOverflowSubtitle_other: 'You are close to the limit in {{count}} categories:',
    },

    CategoryLimitBlock: {
      limitedTitle: 'Category Limits',
      limitedSubtitle: 'Categories for which you have set a limit',
      unlimitedTitle: 'Categories without Limits',
      unlimitedSubtitle: 'Set a limit to keep your spending under control',
    },
  },
}
