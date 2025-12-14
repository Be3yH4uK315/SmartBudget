import { CategoryIcon } from '@features/transactions/components'
import { selectTransactionById } from '@features/transactions/store'
import { CloseOutlined } from '@mui/icons-material'
import { Box, Button, IconButton, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { useAppSelector } from '@shared/store'
import { formatCurrency } from '@shared/utils/formatCurrency'
import dayjs from 'dayjs'
import { useLocation, useNavigate, useParams } from 'react-router'

const TransactionInfo = () => {
  const translate = useTranslate('Transactions.Modal')
  const translateCategory = useTranslate('Categories')
  const navigate = useNavigate()
  const location = useLocation()

  const { id: transactionId } = useParams()

  const transaction = useAppSelector(selectTransactionById(transactionId!))

  if (!transaction) return null

  return (
    <>
      <IconButton
        onClick={() => navigate(-1)}
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

          <Button
            onClick={() =>
              navigate(`./category`, {
                state: { backgroundLocation: location.state?.backgroundLocation || location },
              })
            }
          >
            {translate('changeCategory')}
          </Button>

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
    </>
  )
}

export default TransactionInfo
