import { LocaleDictionary } from '@shared/types'

export const notificationsDict: LocaleDictionary = {
  ru: {
    Notifications: {
      title: 'Уведомления',
      date: '{{date}} в {{time}}',
      unread: 'Новое уведомление',
      markAllAsRead: 'Прочитать все',
      clear: 'Сбросить фильтры',

      NoNotifications: {
        Empty: {
          title: 'Нет уведомлений',
          subtitle: 'Здесь будут отображаться уведомления сервисов',
        },

        Filtered: {
          title: 'Кажется, таких уведомлений нет',
          subtitle: 'Попробуйте убрать лишние фильтры',
        },
      },

      Filters: {
        selected: 'Выбрано: {{value}}',
        clear: 'Сбросить фильтры',
        placeholder: {
          types: 'Тип',
          services: 'Сервис',
          statuses: 'Статус',
        },

        Statuses: {
          read: 'Прочитаны',
          unread: 'Не прочитаны',
          empty: 'Не установлено',
        },

        info: 'Информационные',
        success: 'Успешные',
        alert: 'Предупреждение',
        warning: 'Критические',
        system: 'Системные',

        Goals: 'Цели',
        Transactions: 'Операции',
        Budget: 'Бюджет и лимиты',
        Security: 'Безопасность',
        Limit: 'Лимиты по категориям',
      },

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

        thresholdReached: {
          title: 'Цель почти достигнута',
          message:
            'Цель <strong>"{{name}}"</strong> выполнена на {{percent}}. Вы близки к достижению результата.',
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
        registration: {
          title: 'Регистрация завершена',
          message: 'Аккаунт успешно создан. Добро пожаловать в SmartBudget!',
        },

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

  en: {
    Notifications: {
      title: 'Notifications',
      date: '{{date}} at {{time}}',
      unread: 'New notification',
      markAllAsRead: 'Mark all as read',

      Filters: {
        selected: 'Selected: {{value}}',
        clear: 'Clear filters',
        placeholder: {
          types: 'Type',
          services: 'Service',
          statuses: 'Status',
        },

        Statuses: {
          read: 'Read',
          unread: 'Unread',
          empty: 'Not set',
        },

        info: 'Informational',
        success: 'Successful',
        alert: 'Alert',
        warning: 'Critical',
        system: 'System',

        Goals: 'Goals',
        Transactions: 'Transactions',
        Budget: 'Budget & Limits',
        Security: 'Security',
        Limit: 'Category Limits',
      },

      Limit: {
        preOverflow: {
          title: '80% of category limit reached',
          message:
            'You have used 80% of the monthly limit for category <strong>"{{value}}"</strong>. We recommend monitoring further spending.',
        },

        overflow: {
          title: 'Category limit reached',
          message:
            'The limit for category <strong>"{{value}}"</strong> has been reached. Further spending will exceed the planned budget.',
        },
      },

      Budget: {
        checkResults: {
          title: 'Monthly Results',
          message:
            'The budget month is complete. Review your expenses and plan for the next month.',
        },

        overflow: {
          title: 'Budget limit reached',
          message:
            'You have used the entire monthly budget. Consider reviewing your budget or expenses.',
        },

        preOverflow: {
          title: 'Budget nearing limit',
          message: 'You have used 80% of the total monthly budget. Remaining: {{value}}',
        },

        settingsChanged: {
          title: 'Budget settings changed',
          message: 'New limits are now reflected in the budget',
        },
      },

      Goals: {
        goalCreated: {
          title: 'Goal Created',
          message:
            'Goal <strong>"{{name}}"</strong> has been successfully created. Recommended monthly contribution: {{recommendedPayment}}',
        },

        missedPayment: {
          title: 'Goal contribution missed',
          message:
            'The contribution for goal <strong>"{{name}}"</strong> has not been made this month. This may affect achieving the goal on time.',
        },

        almostAchieved: {
          title: 'Goal nearly achieved',
          message:
            'Goal <strong>"{{name}}"</strong> is 90% complete. You are close to reaching the goal.',
        },

        achieved: {
          title: 'Goal achieved',
          message:
            'Congratulations! Goal <strong>"{{name}}"</strong> has been successfully achieved.',
        },

        expired: {
          title: 'Goal expired',
          message:
            'The deadline for goal <strong>"{{name}}"</strong> has passed. You can extend the deadline or adjust the amount.',
        },

        deadlineIsComing: {
          title: 'Goal deadline approaching',
          message_one:
            'Goal <strong>"{{name}}"</strong> has {{count}} day left until the deadline. Current progress: {{currentPercent}}.',
          message_few:
            'Goal <strong>"{{name}}"</strong> has {{count}} days left until the deadline. Current progress: {{currentPercent}}.',
          message_many:
            'Goal <strong>"{{name}}"</strong> has {{count}} days left until the deadline. Current progress: {{currentPercent}}.',
        },
      },

      Transactions: {
        unclassified: {
          title: 'Uncategorized transactions found',
          message_one:
            '{{count}} transaction is uncategorized. Assign a category for proper budget tracking.',
          message_few:
            '{{count}} transactions are uncategorized. Assign categories for proper budget tracking.',
          message_many:
            '{{count}} transactions are uncategorized. Assign categories for proper budget tracking.',
        },

        categoryChanged: {
          title: 'Transaction category changed',
          message:
            'Transaction category changed from <strong>"{{oldCategory}}"</strong> to <strong>"{{newCategory}}"</strong>.',
        },
      },

      Security: {
        registration: {
          title: 'Registration completed',
          message: 'Your account has been created successfully. Welcome to SmartBudget!',
        },

        passwordChanged: {
          title: 'Password changed',
          message: 'Your account password has been successfully changed.',
        },

        suspiciousActivity: {
          title: 'Suspicious activity detected',
          message:
            'Suspicious activity has been detected in your account. We recommend changing your password immediately.',
        },

        newLogin: {
          title: 'New device login',
          message:
            'Your account was accessed from a new device. If this wasn’t you, we recommend changing your password.',
        },
      },
    },
  },
}
