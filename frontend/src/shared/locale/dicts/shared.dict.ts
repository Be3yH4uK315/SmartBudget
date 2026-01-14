import { LocaleDictionary } from '@shared/types'

export const sharedDict: LocaleDictionary = {
  ru: {
    HeaderTabs: {
      main: 'Главная',
      budget: 'Бюджет',
      goals: 'Цели',
      transactions: 'Операции',
      settings: 'Настройки',
      signIn: 'Войти',
      logout: 'Выход',
    },

    LoadingScreen: {
      loading: 'Загрузка...',
    },

    TransactionsPieBlock: {
      income: 'Пополнения',
      expense: 'Расходы',
      fallback: 'Нет операций за текущий период',
    },
  },

  en: {
    HeaderTabs: {
      main: 'Main',
      budget: 'Budget',
      goals: 'Goals',
      transactions: 'Transactions',
      settings: 'Settings',
      signIn: 'Sign In',
      logout: 'Logout',
    },

    LoadingScreen: {
      loading: 'Loading...',
    },

    TransactionsPieBlock: {
      income: 'Income',
      expense: 'Expense',
      fallback: 'No transactions for the current period',
    },
  },
}
