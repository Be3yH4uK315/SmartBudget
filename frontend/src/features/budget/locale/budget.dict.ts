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

        totalLimitTitle: 'Общий лимит',
        totalLimitSubtitle: 'Сумма, которую планируете потратить',
        totalLimit: 'Сумма',

        addCategory: 'Добавить категорию',
        autoRenew: 'Автопродление',
        create: 'Создать бюджет',

        categoriesTitle: 'Лимиты по категориям',
        categoriesSubtitle: 'Лимит для каждой категории. Можно изменить в настройках бюджета',
        selectPlaceholder: 'Категория',
        limit: 'Лимит категории, руб',
        percentOverflow: 'Лимиты по категориям превышают лимит бюджета на {{value}}%',
        remainingPercent: 'Осталось распределить {{value}}% бюджета',
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
      CategoryBlock: {
        category: '',
        category_one: '',
        category_few: '',
        category_many: '',

        title: '',
        subtitle: '',
      },
    },
  },
}
