import { createLazySliceStateSelector } from '@shared/utils/store'
import { getSecurityInitialState } from './securitySettings.state'

const sliceStateSelector = createLazySliceStateSelector('security', getSecurityInitialState())

export const selectIsPasswordChanging = sliceStateSelector((state) => state.isPasswordChanging)
export const selectSessions = sliceStateSelector((state) => state.sessions)
export const selectIsSessionsLoading = sliceStateSelector((state) => state.isLoading)
export const selectIsDeleteLoading = sliceStateSelector((state) => state.isDeleteLoading)
