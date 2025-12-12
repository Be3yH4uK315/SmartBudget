import { ReactNode } from 'react'
import { store } from '@shared/store'
import { Provider } from 'react-redux'

type Props = {
  children: ReactNode
}

export const ReduxProvider = ({ children }: Props) => {
  return <Provider store={store}>{children}</Provider>
}
