import { LocaleDictionary } from '@shared/types'

export const sharedDict: LocaleDictionary = {
  ru: {
    HeaderTabs: {
      main: 'Главная',
      budget: 'Бюджет',
      goals: 'Цели',
      transactions: 'Операции',
      notifications: 'Уведомления',
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

    ScreenContentComponent: {
      goBack: 'Назад',
    },

    SearchBar: {
      emptyResult: 'К сожалению, ничего не нашлось',
      placeholder: 'Найти...',
    },

    UndefinedScreen: {
      title: 'Такой страницы нет',
      subtitle: 'Возможно, она была удалена, перемещена, или ее адрес указан неверно',
      button: 'Перейти на главную',
    },

    ListDate: {
      today: 'Сегодня',
      yesterday: 'Вчера',
    },
  },

  en: {
    HeaderTabs: {
      main: 'Main',
      budget: 'Budget',
      goals: 'Goals',
      transactions: 'Transactions',
      notifications: 'Notifications',
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

    ScreenContentComponent: {
      goBack: 'Back',
    },
  },
}
