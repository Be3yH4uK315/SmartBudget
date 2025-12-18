import { LocaleDictionary } from '@shared/types'

export const goalsDict: LocaleDictionary = {
  ru: {
    Goals: {
      noGoals: {
        title: 'Целей нет',
        subtitle: 'Здесь можно создать цель и копить на приятные мелочи',
      },

      title: 'Ваши цели',
      create: 'Создать цель',
      edit: 'Сохранить изменения',
      editGoal: 'Редактирвоание Цели',
      createGoal: 'Создание цели',
      date: 'Дата окончания',
      name: 'Название',
      value: 'Сумма',

      GoalsStats: {
        progress: 'Прогресс по всем целям',
        currentValue: 'Сумма накоплений по всем целям',
        targetValue: 'Осталось накопить',
      },

      GoalBlock: {
        currentValue: 'Накоплено: ',
        achieveValue: 'Осталось: ',
        finishDate: 'Дата окончания: ',

        achieved: 'Достигнута',
        expired: 'Просрочена',
        closed: 'Закрыта',
        ongoing: 'В процессе',
      },

      CurrentGoal: {
        GoalStats: {
          daysLeft: 'До завершения цели',
          targetValue: 'Осталось накопить для достижения цели',

          nextPayment: 'Рекомендуем внести для завершения цели',
          nextPayment_one: 'Рекомендуем внести в течение {{count}} дня',
          nextPayment_few: 'Рекомендуем внести в течение {{count}} дней',
          nextPayment_many: 'Рекомендуем внести в течение {{count}} дней',

          day_one: '{{count}} день',
          day_few: '{{count}} дня',
          day_many: '{{count}} дней',
        },
      },
    },
    CurrentGoal: {
      goBack: 'Назад',
      finishDate: 'Дата окончания: {{date}}',
      progress: 'Ваш прогресс по текущей целе',
      autoAdd: 'Подключите автопополнение, чтобы достигать цели быстрее',

      settings: 'Настроить цель',
      settingsSubtitle: 'Редактировать название, сумму цели и дату окончания',

      closeGoal: 'Удалить цель',

      TransactionsPieBlock: {
        title: 'Текущий результат',
        income: 'Пополнения',
        expense: 'Расходы',
      },
    },
  },
  en: {
    Goals: {
      noGoals: {
        title: '',
        subtitle: '',
      },
      title: '',
      create: '',
    },
  },
}
