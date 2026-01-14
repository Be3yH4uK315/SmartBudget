import { useMemo, useState } from 'react'
import { changeCategory, selectCategoryByTransactionId } from '@features/transactions/store'
import { ArrowBackOutlined } from '@mui/icons-material'
import { Button, IconButton, MenuItem, Select, Stack, Typography } from '@mui/material'
import { CategoryOption } from '@shared/components'
import { CATEGORIES_ICONS_MAP, CATEGORY_IDS } from '@shared/constants/categoriesIcons'
import { MODAL_IDS } from '@shared/constants/modals'
import { useTranslate } from '@shared/hooks'
import ModalLayout from '@shared/screens/ModalProvider/ModalLayout'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { openModal } from '@shared/store/modal'

type Props = {
  transactionId: string
}

export const ChangeCategoryModal = ({ transactionId }: Props) => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions.Modal.ChangeCategory')
  const translateCategory = useTranslate('Categories')
  const currentCategory = useAppSelector(selectCategoryByTransactionId(transactionId!))

  const [selectedCategory, setSelectedCategory] = useState<number | null>(null)

  const availableCategories = useMemo(() => {
    if (!currentCategory) return []
    return CATEGORY_IDS.filter((id) => id !== currentCategory)
  }, [currentCategory])

  if (!currentCategory) return null

  const handleConfirm = async () => {
    await dispatch(
      changeCategory({
        transactionId: transactionId!,
        categoryId: Number(selectedCategory),
      }),
    )
    openPrev()
  }

  const openPrev = () =>
    dispatch(
      openModal({ id: MODAL_IDS.TRANSACTION_INFO_MODAL, props: { transactionId: transactionId } }),
    )

  return (
    <ModalLayout>
      <IconButton
        onClick={openPrev}
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
          disabled={!selectedCategory}
          onClick={handleConfirm}
          sx={{ width: '50%' }}
        >
          {translate('confirm')}
        </Button>
      </Stack>
    </ModalLayout>
  )
}
