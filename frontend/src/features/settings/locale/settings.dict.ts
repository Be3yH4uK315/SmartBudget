import { LocaleDictionary } from '@shared/types'

export const settingsDict: LocaleDictionary = {
  ru: {
    Settings: {
      Security: {
        ChangePassword: {
          title: 'Cмена пароля',
          oldPassword: 'Старый пароль',
          newPassword: 'Новый пароль',
          newPasswordConfirm: 'Повторите новый пароль',
          button: 'Сменить пароль',
          forgotPassword: 'Забыл старый пароль',
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
    },
  },
  en: {},
}
