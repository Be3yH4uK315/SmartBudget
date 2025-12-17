import { LocaleDictionary } from '@shared/types'

export const toastsDict: LocaleDictionary = {
  ru: {
    Toasts: {
      error: 'Произошла ошибка',
      success: 'Готово',
      message: {
        noInfo: 'Ошибка при получении данных пользователя',
        cannotChangeCategory: 'Ошибка при смене категории',
        cannotGetTransactions: 'Ошибка при получении транзакций',
        categoryChanged: 'Категория успешно изменена',
      },
    },
  },

  en: {
    Toasts: {
      error: 'An error has occurred',
      success: '',
      message: {
        noInfo: 'Error when receiving user data',
        cannotChangeCategory: '',
        cannotGetTransactions: '',
        categoryChanged: '',
      },
    },
  },
}
