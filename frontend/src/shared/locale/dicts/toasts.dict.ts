import { LocaleDictionary } from '@shared/types'

export const toastsDict: LocaleDictionary = {
  ru: {
    Toasts: {
      error: 'Произошла ошибка',
      message: {
        noInfo: 'Ошибка при получении данных пользователя',
        cannotChangeCategory: 'Ошибка при смене категории',
        cannotGetTransactions: 'Ошибка при получении транзакций',
      },
    },
  },

  en: {
    Toasts: {
      error: 'An error has occurred',
      message: {
        noInfo: 'Error when receiving user data',
        cannotChangeCategory: '',
        cannotGetTransactions: '',
      },
    },
  },
}
