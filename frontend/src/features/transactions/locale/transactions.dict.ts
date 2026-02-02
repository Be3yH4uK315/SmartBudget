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

      today: 'Сегодня',
      yesterday: 'Вчера',

      Filters: {
        selected: 'Выбрано: {{value}}',
        clear: 'Сбросить фильтры',

        placeholder: {
          categories: 'Категории',
          type: 'Тип',
        },

        Popover: {
          button: 'Применить',

          value: {
            emptyLabel: 'Сумма',
            label: 'Сумма от {{from}} до {{to}}',
            from: 'От',
            to: 'До',
          },

          date: {
            emptyLabel: 'Дата',
            label: 'Дата с {{from}} до {{to}}',
            from: 'С',
            to: 'До',
          },
        },

        Date: {
          range: 'с {{from}} по {{to}}',
          from: 'с {{from}}',
          to: 'по {{to}}',
        },

        Value: {
          range: 'от {{from}} до {{to}}',
          from: 'от {{from}}',
          to: 'до {{to}}',
        },

        Type: {
          income: 'Пополнения',
          expense: 'Расходы',
          empty: 'Не установлено',
        },
      },

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

      today: 'Today',
      yesterday: 'Yesterday',

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
