import { LocaleDictionary } from '@shared/types'

export const goalsDict: LocaleDictionary = {
  ru: {
    Goals: {
      NoGoals: {
        Empty: {
          Archive: {
            title: 'Архив пока пуст',
            subtitle: ' ',
          },

          title: 'Нет целей',
          subtitle: 'Здесь можно создать цель и копить на приятные мелочи',
        },

        Filtered: {
          Archive: {
            title: 'Кажется, таких целей нет',
            subtitle: 'Попробуйте убрать лишние фильтры',
          },

          title: 'Кажется, таких целей нет',
          subtitle: 'Попробуйте убрать лишние фильтры',
        },
      },

      title: 'Ваши цели',
      create: 'Создать цель',

      archiveTitle: 'Архив целей',
      goBack: 'Назад',

      Modal: {
        editTitle: 'Редактирвоание Цели',
        editButton: 'Сохранить изменения',

        createTitle: 'Создание цели',
        createButton: 'Создать цель',

        name: 'Название',
        value: 'Сумма',
        date: 'Дата окончания',

        priorityTags: 'Приоритет цели',
        otherTags: 'Прочие тэги',
      },

      Tags: {
        selected: 'Выбрано: {{value}}',
        placeholder: 'Cортировать по тэгам',
        clear: 'Сбросить фильтры',
        archive: 'Архив',

        High: 'Высокий приоритет',
        Medium: 'Средний приоритет',
        Low: 'Низкий Приоритет',
        Health: 'Здоровье',
        Education: 'Образование',
        Sport: 'Спорт',
        Travel: 'Путешествия',
        Home: 'Дом',
        Auto: 'Авто',
        Family: 'Семья',
        Presents: 'Подарки',
        Gadgets: 'Гаджеты',
        Charity: 'Благотворительность',
        RealEstate: 'Недвижимость',
        FinancialCushion: 'Подушка безопасности',
      },

      GoalsStats: {
        progress: 'Прогресс по всем целям',
        currentValue: 'Сумма накоплений по всем целям',
        targetValue: 'Осталось накопить',
      },

      GoalBlock: {
        currentValue: 'Накоплено: {{value}}',
        targetValue: 'Осталось: {{value}}',
        finishDate: 'Дата окончания: {{value}}',
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

    GoalStatus: {
      achieved: 'Достигнута',
      expired: 'Просрочена',
      closed: 'Закрыта',
      ongoing: 'В процессе',

      archived: 'В архиве',
    },

    CurrentGoal: {
      goBack: 'Назад',
      finishDate: 'Дата окончания: {{value}}',
      targetValue: 'Осталось накопить: {{value}}',

      Settings: {
        title: 'Настроить цель',
        subtitle: 'Редактировать название, сумму цели и дату окончания',
      },

      ActionsButtonsBlock: {
        buttonClose: 'Завершить цель',
        buttonRestore: 'Восстановить цель',

        archive: 'Переместить в архив',
        unarchive: 'Вернуть из архива',
      },

      TransactionsPieBlock: {
        title: 'Текущий результат',
        income: 'Пополнения',
        expense: 'Расходы',
      },

      TagsBlock: {
        title: 'Список тэгов',
        subtitle: 'Вы можете добавить или удалить тэги в настройках',
        noTagsSubtitle: 'Вы не установили тэги для этой цели',
        button: 'Установить тэги',
      },

      ProgressBlock: {
        title: 'Ваш прогресс по текущей цели',
        subtitle: 'Подключите автопополнение, чтобы достигать цели быстрее',
      },

      ExpiredBlock: {
        title: 'Цель просрочена',
        subtitle: 'Вы можете установть новую дату окончания цели в настройках',
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
