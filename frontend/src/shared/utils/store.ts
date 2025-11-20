import { AppLazySlices } from '@shared/store'

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
