import { useAuthorization } from '@shared/hooks'
import { LoadingScreen } from '@shared/screens/LoadingScreen'
import { PageRouter } from './PageRouter'
import { Providers } from './providers'
import { RootLayout } from './RootLayout'

export const App = () => {
  return (
    <Providers>
      <RootLayout>
        <Entry />
      </RootLayout>
    </Providers>
  )
}

function Entry() {
  const { isLoading } = useAuthorization()

  return isLoading ? <LoadingScreen /> : <PageRouter />
}
