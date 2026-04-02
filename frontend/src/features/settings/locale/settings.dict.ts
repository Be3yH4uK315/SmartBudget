import { LocaleDictionary } from '@shared/types'

export const settingsDict: LocaleDictionary = {
  ru: {
    Settings: {
      title: 'Настройки',

      Menu: {
        Security: {
          title: 'Безопасность',
          subtitle: 'Пароль и активные сессии',
        },

        Notifications: {
          title: 'Уведомления',
          subtitle: 'Достижение лимитов, целей и другие',
        },

        Budget: {
          title: 'Бюджет',
          subtitle: 'Лимиты по категориям и бюджет',
        },
      },

      Security: {
        ChangePassword: {
          title: 'Смена пароля',
          oldPassword: 'Старый пароль',
          newPassword: 'Новый пароль',
          newPasswordConfirm: 'Повторите новый пароль',
          button: 'Сменить пароль',
          forgotPassword: 'Забыл старый пароль',

          Errors: {
            tooShortPassword: 'Пароль должен содержать минимум 8 символов',
            confirmPassword: 'Подтвердите пароль',
            passwordsNotMatch: 'Пароли не совпадают',
          },
        },

        RefreshDuration: {
          title: 'Автоматически завершать сессию',
          subtitle: 'Если сессия не активна:',
          week: 'Неделю',
          oneMonth: '1 месяц',
          threeMonth: '3 месяца',
          sixMonth: '6 месяцев',
        },

        Sessions: {
          title: 'Активные сессии',
          current: 'Текущая сессия',
          deleteSession: 'Завершить',
          lastActivity: 'Последняя активность: {{date}} в {{time}}',
        },

        title: 'Настройки безопасности',
        deleteOtherSessions: 'Завершить другие сессии',
      },

      Budget: {
        title: 'Настройка бюджета',
        submitButton: 'Сохранить изменения',

        Month: {
          next: 'Бюджет на следующий месяц',
          current: 'Бюджет на текущий месяц',
        },

        Tooltip: {
          info: 'Вы можете либо настроить текущий бюджет, либо заранее задать бюджет на следующий месяц.',
          extraInfo:
            'Опция настройки бюджета на следующий месяц становится доступной с 25-го числа текущего месяца.',
        },

        MonthSwitch: {
          current: 'Текущий',
          next: 'Следующий',
        },
      },

      Notifications: {
        title: 'Настройки уведомлений',
        notificationsStatus: {
          title: 'Допуск уведомлений',
          subtitle: 'Разрешить отправку уведомлений (Отображаются в разделе "Уведомления")',
        },

        pushNotifications: {
          title: 'Push-уведомления',
          subtitle: 'Разрешить отправку push-уведомлений',
        },

        goals: {
          title: 'Цели',
          subtitle: 'Уведомлять о достижении цели, дедлайнах, и прочих действиях',
        },

        transactions: {
          title: 'Операции',
          subtitle:
            'Уведомлять о смене категорий, обнаружении неклассифицированных операциях и т.д.',
        },

        budget: {
          title: 'Бюджет и категории',
          totalLimit: 'Уведомлять о превышении лимита бюджета',
          categoriesLimit: 'Уведомлять о превышении лимита категорий',
        },
      },
    },
  },

  en: {
    Settings: {
      title: 'Settings',

      Menu: {
        Security: {
          title: 'Security',
          subtitle: 'Password and active sessions',
        },

        Notifications: {
          title: 'Notifications',
          subtitle: 'Reaching categories limits, goals etc.',
        },

        Budget: {
          title: 'Budget',
          subtitle: 'Budget and categories limits',
        },
      },

      Security: {
        ChangePassword: {
          title: 'Change password',
          oldPassword: 'Old password',
          newPassword: 'New password',
          newPasswordConfirm: 'Confirm new password',
          button: 'Change password',
          forgotPassword: 'Forgot old password',

          Errors: {
            tooShortPassword: 'The password must contain at least 8 characters',
            confirmPassword: 'Confirm password',
            passwordsNotMatch: "The passwords don't match",
          },
        },

        RefreshDuration: {
          title: 'Automatically logout',
          subtitle: 'If session non-active:',
          week: 'A week',
          oneMonth: '1 month',
          threeMonth: '3 months',
          sixMonth: '6 months',
        },

        Sessions: {
          title: 'Active sessions',
          current: 'Current session',
          deleteSession: 'Revoke',
          lastActivity: 'Last activity: {{date}} at {{time}}',
        },

        title: 'Security settings',
        deleteOtherSessions: 'Revoke other sessions',
      },

      Budget: {},
    },
  },
}
