import { ComponentType } from 'react'
import { SkeletonProps, Stack } from '@mui/material'

type Props = {
  children?: ComponentType<SkeletonProps>
}

export const ScreenSkeleton = ({ children: ContentSkeleton }: Props) => {
  return (
    <Stack width='100%' alignItems={'center'}>
      {ContentSkeleton && <ContentSkeleton />}
    </Stack>
  )
}
