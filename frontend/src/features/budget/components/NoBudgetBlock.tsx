import { Button, Stack, Typography } from '@mui/material'
import { ScreenBackgroundBlock, ScreenContent, StyledPaper } from '@shared/components'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTranslate } from '@shared/hooks'
import { dispatch } from '@shared/store'
import { openModal } from '@shared/store/modal'

export const NoBudgetBlock = () => {
  const translate = useTranslate('Budget.NoBudgetBlock')

  const handleClick = () => {
    dispatch(openModal({ id: MODAL_IDS.CREATE_BUDGET }))
  }

  return (
    <ScreenContent>
      <ScreenBackgroundBlock />

      <StyledPaper paperSx={{ zIndex: 20, mt: 10, textAlign: 'center' }}>
        <Stack spacing={4}>
          <Stack spacing={2}>
            <Typography variant="h3">{translate('title')}</Typography>

            <Typography>{translate('subtitle')}</Typography>
          </Stack>

          <Button onClick={handleClick}>{translate('create')}</Button>
        </Stack>
      </StyledPaper>
    </ScreenContent>
  )
}
