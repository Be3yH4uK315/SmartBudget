import { PageRouter } from './PageRouter'
import { Providers } from './providers'
import { RootLayout } from './RootLayout'

export const App = () => {
  return (
    <Providers>
      <RootLayout>
        <PageRouter />
      </RootLayout>
    </Providers>
  )
}
