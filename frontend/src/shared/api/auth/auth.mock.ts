const delay = (ms = 900) => new Promise((res) => setTimeout(res, ms))

class AuthMock {
  async verifyEmail(payload: VerifyEmail): Promise<string> {
    await delay()
    return 'sign_up'
  }

  async verifyLink(params: VerifyLink): Promise<boolean> {
    await delay()
    return true
  }

  async completeRegistration(payload: CompleteRegistration): Promise<boolean> {
    await delay()
    return true
  }

  async login(payload: Login): Promise<any> {
    await delay()

    const err: any = new Error('Wrong password')
    err.status = 403
    throw err
  }

  async logout(): Promise<boolean> {
    await delay()
    return true
  }

  async resetPassword(payload: ResetPassword): Promise<boolean> {
    await delay()
    return true
  }

  async completeReset(payload: CompleteReset): Promise<boolean> {
    await delay()
    return true
  }

  async refresh(): Promise<boolean> {
    await delay()
    return true
  }

  async validateToken(token: string): Promise<boolean> {
    await delay()
    return true
  }
}

export const authMock = new AuthMock()