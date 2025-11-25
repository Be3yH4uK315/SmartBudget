/** Тип описывающий пользователя */
type User = {
  /** ID пользователя */
  id: string

  /** Роль пользователя */
  role: 0 | 1

  /** Имя пользователя */
  name: string

  email: string
}
