import React from 'react'
import { CategoryIcon } from '@features/transactions/components'
import { Transaction } from '@features/transactions/types'
import { AccessTimeOutlined, ErrorOutlineOutlined } from '@mui/icons-material'
import { Box, Stack, Typography } from '@mui/material'
import { TypographyWithAdornment } from '@shared/components'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTheme, useTranslate } from '@shared/hooks'
import { useAppDispatch } from '@shared/store'
import { openModal } from '@shared/store/modal'
import { formatCurrency } from '@shared/utils'

type Props = {
  transaction: Transaction
}

export const TransactionLine = React.memo(function TransactionLine({ transaction }: Props) {
  const translate = useTranslate('Transactions')
  const translateCategory = useTranslate('Categories')
  const dispatch = useAppDispatch()
  const theme = useTheme()

  const handleClick = () =>
    dispatch(
      openModal({
        id: MODAL_IDS.TRANSACTION_INFO_MODAL,
        props: { transactionId: transaction.transactionId },
      }),
    )

  const color =
    transaction.status === 'pending'
      ? 'gray.main'
      : transaction.status === 'rejected'
        ? 'error.main'
        : transaction.type === 'income'
          ? 'success.main'
          : 'text.primary'

  const hoverColor = theme.colorMode === 'light' ? 'surface.dark' : 'surface.light'

  const iconBgColor = theme.colorMode === 'light' ? 'gray.light' : 'surface.light'
  const iconColor = theme.colorMode === 'light' ? 'gray.dark' : 'text.primary'

  const Icon =
    transaction.status === 'pending'
      ? AccessTimeOutlined
      : transaction.status === 'rejected'
        ? ErrorOutlineOutlined
        : undefined

  return (
    <Box
      sx={{
        display: 'flex',
        width: '100%',
        justifyContent: 'space-between',
        cursor: 'pointer',
        ':hover': { bgcolor: hoverColor },
        p: 1,
        px: 2,
        borderRadius: '12px',
      }}
      onClick={handleClick}
    >
      <Stack direction={'row'} spacing={2} alignItems={'center'}>
        <CategoryIcon
          categoryId={transaction.categoryId}
          size={48}
          boxSx={{ p: 1, width: 'max-content', height: 'max-content', bgcolor: iconBgColor }}
          iconSx={{ color: iconColor }}
        />

        <Stack>
          <Typography variant="h5">{transaction.name}</Typography>

          <Typography variant="caption">{translateCategory(transaction.categoryId)}</Typography>
        </Stack>
      </Stack>

      <Stack sx={{ textAlign: 'right', alignItems: 'end' }}>
        <TypographyWithAdornment
          text={formatCurrency(transaction.value, transaction.type)}
          position="end"
          typographyVariant="h5"
          typographySx={{ textAlign: 'right', whiteSpace: 'nowrap' }}
          color={color}
          Icon={Icon}
        />

        <Typography variant="caption">{translate('debitCard')}</Typography>
      </Stack>
    </Box>
  )
})
