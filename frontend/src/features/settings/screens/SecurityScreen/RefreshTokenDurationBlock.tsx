import { REFRESH_TOKEN_VALUES } from '@features/settings/constants/refreshTokenForm'
import {
  selectIsRefreshLoading,
  selectRefreshTokenDuration,
  setRefreshTokenDuration,
} from '@features/settings/store/security'
import { RefreshTokenFormItem } from '@features/settings/types'
import { RadioButtonUnchecked } from '@mui/icons-material'
import { FormControl, FormControlLabel, Radio, RadioGroup, Stack, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'

export const RefreshTokenDurationBlock = () => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Settings.RefreshDuration')

  const checkedDuration = useAppSelector(selectRefreshTokenDuration)
  const isLoading = useAppSelector(selectIsRefreshLoading)

  const handleDurationChange = (value: number) => {
    dispatch(setRefreshTokenDuration({ days: value }))
  }

  const renderRadio = (item: RefreshTokenFormItem) => {
    return (
      <FormControlLabel
        key={item.value}
        value={item.value}
        label={translate(item.label)}
        checked={item.value === checkedDuration}
        onChange={() => handleDurationChange(item.value)}
        control={
          <Radio icon={<RadioButtonUnchecked sx={{ color: 'text.primary' }} />} sx={{ pr: 1 }} />
        }
        sx={{ m: 0 }}
      />
    )
  }

  return (
    <>
      {checkedDuration > 0 && (
        <StyledPaper elevation={0}>
          <FormControl disabled={isLoading}>
            <Typography variant="h4">{translate('title')}</Typography>

            <Typography variant="caption">{translate('subtitle')}</Typography>

            <RadioGroup>
              <Stack direction={{ xs: 'column', md: 'row' }} spacing={{ xs: 0, md: 2 }}>
                {REFRESH_TOKEN_VALUES.map(renderRadio)}
              </Stack>
            </RadioGroup>
          </FormControl>
        </StyledPaper>
      )}
    </>
  )
}
