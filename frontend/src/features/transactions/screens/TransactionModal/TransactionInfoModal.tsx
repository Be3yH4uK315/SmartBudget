import { CategoryIcon } from '@features/transactions/components'
import { selectTransactionById } from '@features/transactions/store'
import { CloseOutlined } from '@mui/icons-material'
import { Box, Button, IconButton, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { ModalLayout } from '@shared/screens/ModalProvider/ModalLayout'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { formatCurrency } from '@shared/utils/formatCurrency'
import dayjs from 'dayjs'

type Props = {
  transactionId: string
  onClose: () => void
}

export const TransactionInfoModal = ({ transactionId, onClose }: Props) => {
  const translate = useTranslate('Transactions.Modal')
  const translateCategory = useTranslate('Categories')
  const dispatch = useAppDispatch()

  const transaction = useAppSelector(selectTransactionById(transactionId!))

  const handleChangeCategory = () =>
    dispatch(
      openModal({ id: 'changeTransactionCategory', props: { transactionId: transactionId } }),
    )

  if (!transaction) return null

  return (
    <ModalLayout>
      <IconButton
        onClick={onClose}
        sx={{
          position: 'absolute',
          top: 12,
          right: 12,
        }}
      >
        <CloseOutlined sx={{ color: 'link.main' }} />
      </IconButton>

      <Stack spacing={4} sx={{ p: 3, alignItems: 'center' }}>
        <Typography fontWeight={'600'}>
          {dayjs(transaction.date).format('DD.MM.YYYY, hh:mm:ss')}
        </Typography>

        <CategoryIcon categoryId={transaction.categoryId} />

        <Stack spacing={1} sx={{ alignItems: 'center', textAlign: 'center', width: '100%' }}>
          <Typography>{transaction.name}</Typography>

          <Typography variant="caption">{`${translateCategory(transaction.categoryId)}, MCC ${transaction.mcc}`}</Typography>

          <Typography variant="h4">
            {formatCurrency(transaction.value, transaction.type)}
          </Typography>

          <Button onClick={handleChangeCategory}>{translate('changeCategory')}</Button>

          <Box
            sx={{
              display: 'flex',
              whiteSpace: 'pre-wrap',
              p: 2.5,
              bgcolor: 'surface.light',
              width: '60%',
              minHeight: '150px',
              borderRadius: '24px',
            }}
          >
            <Typography>{transaction.description}</Typography>
          </Box>
        </Stack>
      </Stack>
    </ModalLayout>
  )
}
