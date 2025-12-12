import { ComponentType, useEffect } from 'react'
import { useAppSelector } from '@shared/store'
import { selectUser } from '@shared/store/user'
import { useNavigate } from 'react-router'

/**
 * HOC для проверки авторизации.
 */
export function withAuth<P extends object>(WrappedComponent: ComponentType<P>) {
  return function AuthWrapper(props: P) {
    const navigate = useNavigate()

    const { isAuth } = useAppSelector(selectUser)

    useEffect(() => {
      if (!isAuth) {
        navigate('/auth/sign-in', {
          replace: true,
        })
      }
    }, [isAuth, navigate])

    if (!isAuth) {
      return null
    }

    return <WrappedComponent {...props} />
  }
}
