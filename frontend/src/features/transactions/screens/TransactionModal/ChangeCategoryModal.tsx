import { useMemo, useState } from 'react'
import { changeCategory, selectIsCategoryChanging } from '@features/transactions/store'
import { Category, Transaction } from '@features/transactions/types'
import { ArrowBackOutlined } from '@mui/icons-material'
import {
  Button,
  CircularProgress,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Typography,
} from '@mui/material'
import { CategoryOption } from '@shared/components'
import { CATEGORIES_ICONS_MAP, CATEGORY_IDS, MODAL_IDS } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import ModalLayout from '@shared/screens/ModalProvider'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'

type Props = {
  transaction: Transaction
}

export const ChangeCategoryModal = ({ transaction }: Props) => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions.Modal.ChangeCategory')
  const translateCategory = useTranslate('Categories')

  const isCategoryChanging = useAppSelector(selectIsCategoryChanging)
  const currentCategory = transaction.categoryId

  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)

  const availableCategories = useMemo(() => {
    if (!currentCategory) return []
    return CATEGORY_IDS.filter((id) => id !== currentCategory)
  }, [currentCategory])

  if (!currentCategory) return null

  const handleConfirm = async () => {
    await dispatch(
      changeCategory({
        transactionId: transaction.transactionId,
        categoryId: selectedCategory as Category,
      }),
    ).unwrap()

    openPrev({ ...transaction, categoryId: selectedCategory as Category })
  }

  const openPrev = (transaction: Transaction) =>
    dispatch(
      openModal({ id: MODAL_IDS.TRANSACTION_INFO_MODAL, props: { transaction: transaction } }),
    )

  return (
    <ModalLayout>
      <IconButton
        onClick={() => openPrev(transaction)}
        sx={{
          position: 'absolute',
          top: 12,
          left: 12,
        }}
      >
        <ArrowBackOutlined sx={{ color: 'link.main' }} />
      </IconButton>

      <Stack spacing={4} sx={{ p: 3, alignItems: 'center' }}>
        <Typography variant="h4">{translate('title')}</Typography>

        <Stack spacing={1} alignItems={'center'}>
          <Typography>{translate('currentCategory')}</Typography>

          <Typography>{translateCategory(currentCategory)}</Typography>
        </Stack>

        <Select
          sx={{ width: '50%', bgcolor: 'surface.light' }}
          value={selectedCategory ?? ''}
          displayEmpty
          onChange={(e) => setSelectedCategory(Number(e.target.value))}
          renderValue={(value) => {
            if (!value) return translate('selectPlaceholder')

            const Icon = CATEGORIES_ICONS_MAP.get(value)!

            return <CategoryOption value={value} Icon={Icon} />
          }}
        >
          {availableCategories.map((categoryId) => {
            const Icon = CATEGORIES_ICONS_MAP.get(categoryId)
            return (
              <MenuItem key={categoryId} value={String(categoryId)}>
                <CategoryOption value={categoryId} Icon={Icon} />
              </MenuItem>
            )
          })}
        </Select>

        <Button
          variant="yellow"
          disabled={!selectedCategory || isCategoryChanging}
          onClick={handleConfirm}
          sx={{ width: '50%' }}
        >
          {isCategoryChanging ? (
            <CircularProgress size={20} sx={{ color: '#333' }} />
          ) : (
            translate('confirm')
          )}
        </Button>
      </Stack>
    </ModalLayout>
  )
}
