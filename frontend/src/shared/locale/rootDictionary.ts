export const rootDictionary: LocaleDictionary = {
  ru: {
    AuthScreen: {
      email: {
        title: 'Вход',
        subtitle: 'Введите почту, чтобы войти или зарегистрироваться',
        placeholder: 'Электронная почта',
      },

      password: {
        title: 'Введите пароль',
        placeholder: 'Пароль',
        forgotPassword: 'Не помню пароль',
        wrongPassword: 'Неверный пароль',
        tooManyAttempts: 'Слишком много попыток, попробуйте позже',
      },

      verifyEmail: {
        title: 'Проверьте почту',
        subtitleEmail: 'Письмо с подтверждением регистрации отправлено на почту {{email}}',
        subtitlePassword: 'Письмо для смены пароля отправлено на почту {{email}}',
        buttonText: 'Письмо не пришло',
      },

      signIn: 'Войти',
    },

    RegistrationScreen: {
      title: 'Регистрация',
      caption: 'Нажимая кнопку «Зарегистрироваться» вы соглашаетесь с условиями использования.',
      name: 'Имя',
      country: 'Страна',
      password: 'Пароль',
      repeatPassword: 'Подтвердите пароль',
      passwordsNotMatch: 'Пароли не совпадают',
      continue: 'Зарегистрироваться',
    },

    ResetPasswordScreen: {
      title: 'Восстановление пароля',
      password: 'Пароль',
      repeatPassword: 'Подтвердите пароль',
      passwordsNotMatch: 'Пароли не совпадают',
      continue: 'Сбросить пароль',
    },

    WrongLink: {
      incorrectLink: 'К сожалению, эта страница недоступна',
      incorrectLinkCaption: 'Проверьте корректность ссылки или попробуйте еще раз',
    },

    HeaderTabs: {
      main: 'Главная',
      budget: 'Бюджет',
      goals: 'Цели',
      transactions: 'Операции',
      settings: 'Настройки',
      signIn: 'Войти',
      logout: 'Выход',
    },

    LoadingScreen: {
      loading: 'Загрузка...',
    },

    Categories: {
      0: 'Кафе и рестораны',
      1: 'Развлечения',
      2: 'Супермаркеты',
      3: 'Транспорт',
      4: 'ЖКХ',
      5: 'Маркетплейсы',
      6: 'Автомобиль',
      7: 'Аптеки',
      8: 'Красота и здоровье',
      9: '',
      10: '',
      11: '',
      12: '',
      13: '',
      14: '',
      15: '',
      16: '',
      17: '',
    },

    Dashboard: {
      greeting: 'Здравствуйте, {{name}}!',

      Goal: {
        title: 'Цели',
        emptyTitle: 'Нет активных целей',
        createButton: 'Создать цель',
      },

      Budget: {
        title: 'Бюджет',
        emptyTitle: 'Нет бюджета',
        createButton: 'Создать бюджет',
      },

      Transactions: {
        transactions: 'Операции в',
        income: 'Пополнения',
        expense: 'Расходы',
        month: {
          0: 'январе',
          1: 'феврале',
          2: 'марте',
          3: 'апреле',
          4: 'мае',
          5: 'июне',
          6: 'июле',
          7: 'августе',
          8: 'сентябре',
          9: 'октябре',
          10: 'ноябре',
          11: 'декабре',
        },
        fallback: 'Нет операций за текущий период',
      },

      Buttons: {
        Profile: {
          title: 'Профиль',
          subtitle: 'Данные профиля и уведомления',
        },
        Security: {
          title: 'Безопасность',
          subtitle: 'Пароль и активные сессии',
        },
        Budget: {
          title: 'Бюджет',
          subtitle: 'Настроить бюджет',
        },
        Goals: {
          title: 'Цели',
          subtitle: 'Создать или настроить цель',
        },
      },
    },
  },

  en: {
    AuthScreen: {
      email: {
        title: 'Login',
        subtitle: 'Enter your email to sign in or sign up',
        placeholder: 'Email address',
      },
      password: {
        title: 'Hello, {{name}}',
        placeholder: 'Password',
        forgotPassword: 'Forgot password',
      },
      verifyEmail: {
        title: 'Check your Inbox',
        subtitle: 'A confirmation email has been sent to {{email}}',
        buttonText: 'Resend confirmation mail',
      },
      signIn: 'Sign In',
    },
    HeaderTabs: {
      main: 'Main',
      budget: 'Budget',
      goals: 'Goals',
      transactions: 'Transactions',
      settings: 'Settings',
      signIn: 'Sign In',
      logout: 'Logout',
    },
    LoadingScreen: {
      loading: 'Loading...',
    },
  },
}
