import { LocaleDictionary } from '@shared/types'

export const notificationsDict: LocaleDictionary = {
  ru: {
    Notifications: {
      title: 'Уведомления',
      date: '{{date}} в {{time}}',
      unread: 'Новое уведомление',
      markAllAsRead: 'Прочитать все',

      Limit: {
        preOverflow: {
          title: 'Достижение 80% лимита категории',
          message:
            'По категории <strong>"{{value}}"</strong> использовано 80% месячного лимита. Рекомендуем контролировать дальнейшие расходы.',
        },

        overflow: {
          title: 'Достижение лимита категории',
          message:
            'Лимит по категории <strong>"{{value}}"</strong> исчерпан. Дальнейшие расходы превысят запланированный бюджет.',
        },
      },

      Budget: {
        checkResults: {
          title: 'Результаты месяца',
          message:
            'Бюджетный месяц завершён. Ознакомьтесь с итогами расходов и планом на следующий месяц.',
        },

        overflow: {
          title: 'Достигнут лимит бюджета',
          message:
            'Вы использовали весь месячный бюджет. Рекомендуем пересмотреть бюджет или расходы.',
        },

        preOverflow: {
          title: 'Бюджет близок к исчерпанию',
          message: 'Вы использовали 80% общего месячного бюджета. Остаток: {{value}}',
        },

        settingsChanged: {
          title: 'Настройки бюджета изменены',
          message: 'Новые лимиты уже отражены в бюджете',
        },
      },

      Goals: {
        goalCreated: {
          title: 'Создание цели',
          message:
            'Цель <strong>"{{name}}"</strong> успешно создана. Рекомендуемый ежемесячный взнос: {{recommendedPayment}}',
        },

        missedPayment: {
          title: 'Взнос по цели не внесён',
          message:
            'В текущем месяце взнос по цели <strong>"{{name}}"</strong> ещё не внесён. Это может повлиять на достижение цели в срок.',
        },

        almostAchieved: {
          title: 'Цель почти достигнута',
          message:
            'Цель <strong>"{{name}}"</strong> выполнена на 90%. Вы близки к достижению результата.',
        },

        achieved: {
          title: 'Цель достигнута',
          message: 'Поздравляем! Цель <strong>"{{name}}"</strong> успешно достигнута.',
        },

        expired: {
          title: 'Цель просрочена',
          message:
            'Срок цели <strong>"{{name}}"</strong> истёк. Вы можете продлить дедлайн или скорректировать сумму.',
        },

        deadlineIsComing: {
          title: 'Скоро дедлайн цели',
          message_one:
            'До дедлайна цели <strong>"{{name}}"</strong> остался {{count}} день. Текущий прогресс: {{currentPercent}}.',
          message_few:
            'До дедлайна цели <strong>"{{name}}"</strong> осталось {{count}} дня. Текущий прогресс: {{currentPercent}}.',
          message_many:
            'До дедлайна цели <strong>"{{name}}"</strong> осталось {{count}} дней. Текущий прогресс: {{currentPercent}}.',
        },
      },

      Transactions: {
        unclassified: {
          title: 'Обнаружены транзакции без категории',
          message_one:
            'Обнаружена {{count}} транзакция без категории. Назначьте категорию для корректного учёта бюджета.',
          message_few:
            'Обнаружены {{count}} транзакции без категории. Назначьте категорию для корректного учёта бюджета.',
          message_many:
            'Обнаружены {{count}} транзакций без категории. Назначьте категорию для корректного учёта бюджета.',
        },

        categoryChanged: {
          title: 'Категория транзакции изменена',
          message:
            'Категория транзакции изменена с <strong>"{{oldCategory}}"</strong> на <strong>"{{newCategory}}"</strong>.',
        },
      },

      Security: {
        passwordChanged: {
          title: 'Пароль изменен',
          message: 'Пароль аккаунта успешно изменён.',
        },

        suspiciousActivity: {
          title: 'Подозрительная активность',
          message:
            'Обнаружена подозрительная активность в аккаунте. Рекомендуем немедленно сменить пароль.',
        },

        newLogin: {
          title: 'Вход с нового устройства',
          message:
            'Выполнен вход в аккаунт с нового устройства. Если это были не вы — рекомендуем сменить пароль.',
        },
      },
    },
  },

  en: {},
}
