import { ComponentType, useEffect } from 'react'
import { useSelector } from 'react-redux'
import { selectUser } from '@shared/store/user'
import { useNavigate } from 'react-router'

/**
 * HOC для проверки авторизации.
 */
export function withAuth<P extends object>(WrappedComponent: ComponentType<P>) {
  return function AuthWrapper(props: P) {
    const navigate = useNavigate()

    const { isAuth } = useSelector(selectUser)

    useEffect(() => {
      if (!isAuth) {
        navigate('/sign-in', {
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
