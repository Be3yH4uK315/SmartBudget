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
        title: 'Enter your password',
        placeholder: 'Password',
        forgotPassword: 'Forgot password',
        wrongPassword: 'Incorrect password',
        tooManyAttempts: 'Too many attempts, please try again later',
      },

      verifyEmail: {
        title: 'Check your email',
        subtitleEmail: 'A registration confirmation email has been sent to {{email}}',
        subtitlePassword: 'A password reset email has been sent to {{email}}',
        buttonText: 'Didn’t receive the email?',
      },

      signIn: 'Sign In',
    },

    RegistrationScreen: {
      title: 'Registration',
      caption: 'By clicking "Register" you agree to the terms of use',
      name: 'Name',
      country: 'Country',
      password: 'Password',
      repeatPassword: 'Confirm password',
      passwordsNotMatch: 'Passwords do not match',
      continue: 'Register',
    },

    ResetPasswordScreen: {
      title: 'Password Recovery',
      password: 'Password',
      repeatPassword: 'Confirm password',
      passwordsNotMatch: 'Passwords do not match',
      continue: 'Reset Password',
    },

    WrongLink: {
      incorrectLink: 'Unfortunately, this page is unavailable',
      incorrectLinkCaption: 'Please check the link or try again',
    },
  },
}
