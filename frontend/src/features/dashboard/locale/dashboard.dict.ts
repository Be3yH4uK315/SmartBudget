import { LocaleDictionary } from '@shared/types'

export const dashboardDict: LocaleDictionary = {
  ru: {
    Dashboard: {
      greeting: 'Здравствуйте, {{name}}!',

      Goal: {
        title: 'Цели',
        emptyTitle: 'Нет активных целей',
        createButton: 'Создать цель',
      },

      Budget: {
        title: 'Бюджет',
        emptyTitle: 'Нет бюджета',
        createButton: 'Создать бюджет',
      },

      Transactions: {
        transactions: 'Операции в',
        income: 'Пополнения',
        expense: 'Расходы',
        month: {
          0: 'январе',
          1: 'феврале',
          2: 'марте',
          3: 'апреле',
          4: 'мае',
          5: 'июне',
          6: 'июле',
          7: 'августе',
          8: 'сентябре',
          9: 'октябре',
          10: 'ноябре',
          11: 'декабре',
        },
        fallback: 'Нет операций за текущий период',
      },

      Buttons: {
        Profile: {
          title: 'Профиль',
          subtitle: 'Данные профиля и уведомления',
        },
        Security: {
          title: 'Безопасность',
          subtitle: 'Пароль и активные сессии',
        },
        Budget: {
          title: 'Бюджет',
          subtitle: 'Настроить бюджет',
        },
        Goals: {
          title: 'Цели',
          subtitle: 'Создать или настроить цель',
        },
      },
    },
  },

  en: {
    Dashboard: {
      greeting: 'Hello, {{name}}!',

      Goal: {
        title: 'Goals',
        emptyTitle: 'There are no active goals',
        createButton: 'New goal',
      },

      Budget: {
        title: 'Budget',
        emptyTitle: 'There is no active budget',
        createButton: 'Create budget',
      },

      Transactions: {
        transactions: 'Transactions in',
        income: 'Income',
        expense: 'Expense',
        month: {
          0: 'January',
          1: 'February',
          2: 'March',
          3: 'April',
          4: 'May',
          5: 'June',
          6: 'July',
          7: 'August',
          8: 'September',
          9: 'October',
          10: 'November',
          11: 'December',
        },
        fallback: 'No transactions for the current period',
      },

      Buttons: {
        Profile: {
          title: 'Profile',
          subtitle: 'Profile data and notifications',
        },
        Security: {
          title: 'Security',
          subtitle: 'Password and active sessions',
        },
        Budget: {
          title: 'Budget',
          subtitle: 'Set up a budget',
        },
        Goals: {
          title: 'Goals',
          subtitle: 'Create or configure a goal',
        },
      },
    },
  },
}
