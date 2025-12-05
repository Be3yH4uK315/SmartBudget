import { ReactNode, useMemo } from 'react'
import { useTranslate } from '@shared/hooks'
import { createAppStore } from '@shared/store/store'
import { Provider } from 'react-redux'

type Props = {
  children: ReactNode
}

export const ReduxProvider = ({ children }: Props) => {
  const translate = useTranslate('Error')
  const store = useMemo(() => createAppStore(translate), [translate])

  return <Provider store={store}>{children}</Provider>
}
