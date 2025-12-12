import { AppLazySlices } from '@shared/store'
import { RootState } from '@shared/types'

export function createLazySliceStateSelector<SliceName extends keyof AppLazySlices>(
  sliceName: SliceName,
  defaultState: AppLazySlices[SliceName],
) {
  return function lazySliceStateSelector<T>(
    selector: (sliceState: AppLazySlices[SliceName], rootState: RootState) => T,
  ) {
    return (rootState: RootState) => selector(rootState[sliceName] ?? defaultState, rootState)
  }
}
