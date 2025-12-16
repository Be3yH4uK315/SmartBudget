import { LocaleDictionary } from '@shared/types'

export const transactionsDict: LocaleDictionary = {
  ru: {
    Transactions: {
      title: 'Операции',
      debitCard: 'Дебетовая карта',
      noTransactions: 'Нет транзакций',
      loading: 'Загрузка...',
      loadMore: 'Загрузить еще',
      emptyCategory: 'Сбросить фильтр',
      categoryFilter: 'Категория',

      Modal: {
        changeCategory: 'Сменить категорию',

        ChangeCategory: {
          title: 'Смена категории',
          currentCategory: 'Текущая категория:',
          confirm: 'Сменить категорию',
          selectPlaceholder: 'Новая категория',
        },
      },
    },
  },
  en: {
    Transactions: {
      title: 'Transactions',
      debitCard: 'Debit card',
      noTransactions: 'There is no transactions',
      loading: 'Loading...',
      loadMore: 'Load more',

      Modal: {
        changeCategory: 'Change category',

        ChangeCategory: {
          title: 'Category change',
          currentCategory: 'Current category',
          confirm: 'Change category',
          selectPlaceholder: 'New category',
        },
      },
    },
  },
}
