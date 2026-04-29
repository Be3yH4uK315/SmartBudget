import { createBudget } from '@features/budget/store'
import { Button, Stack, Typography } from '@mui/material'
import { BudgetForm } from '@shared/components'
import { useBudgetForm, useTranslate } from '@shared/hooks'
import ModalLayout from '@shared/screens/ModalProvider'
import { useAppDispatch } from '@shared/store'
import { mapFormToBudgetPayload } from '@shared/utils'

type Props = {
  onClose: () => void
}

export const CreateBudgetModal = ({ onClose }: Props) => {
  const translate = useTranslate('Budget.Modal')
  const dispatch = useAppDispatch()

  const props = useBudgetForm()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const payload = mapFormToBudgetPayload(props.values)
    dispatch(createBudget({ payload: payload }))
    onClose()
  }

  return (
    <ModalLayout>
      <Stack spacing={3}>
        <Typography variant="h2">{translate('createTitle')}</Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={3}>
            <BudgetForm {...props} />

            <Button type="submit" variant="yellow" disabled={!props.canSubmit()}>
              {translate('submitButton')}
            </Button>
          </Stack>
        </form>
      </Stack>
    </ModalLayout>
  )
}
