import { LocaleDictionary } from '@shared/types'

export const authDict: LocaleDictionary = {
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
      caption: 'Нажимая кнопку «Зарегистрироваться» вы соглашаетесь с условиями использования',
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

    RegistrationScreen: {
      title: 'Registration',
      caption: 'By clicking the "Register" button, you agree to the terms of use',
      name: 'Name',
      country: 'Country',
      password: 'Password',
      repeatPassword: 'Confirm the password',
      passwordsNotMatch: 'Passwords do not match',
      continue: 'Register',
    },

    ResetPasswordScreen: {
      title: 'Password Recovery',
      password: 'Password',
      repeatPassword: 'Confirm the password',
      passwordsNotMatch: 'Passwords do not match',
      continue: 'Reset password',
    },

    WrongLink: {
      incorrectLink: 'Unfortunately, this page is unavailable.',
      incorrectLinkCaption: 'Check the correctness of the link or try again',
    },
  },
}
