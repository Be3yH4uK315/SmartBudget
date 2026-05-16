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
      createTransaction: 'Создать транзакцию',
      importTransactions: 'Импортировать транзакции',

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

        AddTransaction: {
          title: 'Создание транзакции',
          selectPlaceholder: 'Выберите категорию',
          infoBlock: 'Необходимо перезагрузить страницу после добавления транзакции',

          goal: 'Цель "{{name}}"',
          accountId: 'ID цели',
          amount: 'Сумма',
          date: 'Дата',
          type: 'Тип транзакции',
          status: 'Статус транзакции',
          description: 'Описание транзакции',
          mcc: 'MCC',
          merchant: 'Продавец',

          Types: {
            income: 'Доход',
            expense: 'Расход',
          },

          Statuses: {
            confirmed: 'Исполнена',
            rejected: 'Отклонена',
            pending: 'В обработке',
          },

          confirm: 'Создать',
        },
      },
    },
  },

  en: {
    Transactions: {
      title: 'Transactions',
      debitCard: 'Debit Card',
      noTransactions: 'No transactions',
      loading: 'Loading...',
      loadMore: 'Load more',
      emptyCategory: 'Clear filter',
      categoryFilter: 'Category',

      today: 'Today',
      yesterday: 'Yesterday',

      Filters: {
        selected: 'Selected: {{value}}',
        clear: 'Clear filters',

        placeholder: {
          categories: 'Categories',
          type: 'Type',
        },

        Popover: {
          button: 'Apply',

          value: {
            emptyLabel: 'Amount',
            label: 'Amount from {{from}} to {{to}}',
            from: 'From',
            to: 'To',
          },

          date: {
            emptyLabel: 'Date',
            label: 'Date from {{from}} to {{to}}',
            from: 'From',
            to: 'To',
          },
        },

        Date: {
          range: 'from {{from}} to {{to}}',
          from: 'from {{from}}',
          to: 'to {{to}}',
        },

        Value: {
          range: 'from {{from}} to {{to}}',
          from: 'from {{from}}',
          to: 'to {{to}}',
        },

        Type: {
          income: 'Income',
          expense: 'Expense',
          empty: 'Not set',
        },
      },

      Modal: {
        changeCategory: 'Change category',

        ChangeCategory: {
          title: 'Change Category',
          currentCategory: 'Current category:',
          confirm: 'Change category',
          selectPlaceholder: 'New category',
        },
      },
    },
  },
}
