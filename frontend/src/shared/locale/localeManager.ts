import { user_api } from '@shared/api/user'
import { getState } from '@shared/store'
import { Languages, OneLocaleDictionary } from '@shared/types'
import dayjs from 'dayjs'
import { showToast } from '../utils'
import { initI18n } from './localization.config'

class LocaleManager {
  private readonly i18n = initI18n()

  constructor() {
    dayjs.locale(this.i18n.language)
  }

  getLocale(): Languages {
    return this.i18n.language as Languages
  }

  async updateLocale(lang?: Languages, extraDict?: OneLocaleDictionary) {
    const nextLang = lang ?? (this.i18n.language as Languages)
    const isAuth = getState().user.isAuth

    if (extraDict) {
      const current = this.i18n.getResourceBundle(nextLang, 'translation') || {}
      this.i18n.addResources(nextLang, 'translation', {
        ...current,
        ...extraDict,
      })
    }

    await this.i18n.changeLanguage(nextLang)

    dayjs.locale(nextLang)
    localStorage.setItem('language', nextLang)

    if (isAuth) {
      user_api
        .updateUserLang(nextLang)
        .catch(() => showToast({ messageKey: 'cannotUpdateLang', type: 'warning' }))
    }
  }

  translate(key: string, params?: Record<string, unknown>): string {
    return this.i18n.t(key, params)
  }
}

/**
 * !!! НЕ ИСПОЛЬЗОВАТЬ снаружи shared/locale.
 * Только через провайдеры и хуки.
 */
export const _localeManager = new LocaleManager()
