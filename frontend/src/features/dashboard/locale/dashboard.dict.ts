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

      TransactionsPieBlock: {
        title: 'Операции в',
        income: 'Пополнения',
        expense: 'Расходы',
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

      TransactionsPieBlock: {
        title: 'Transactions in',
        income: 'Income',
        expense: 'Expense',
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
