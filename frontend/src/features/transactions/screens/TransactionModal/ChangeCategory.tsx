import { LazyExoticComponent, Suspense, useMemo, useState } from 'react'
import {
  CATEGORIES_ICONS_MAP,
  CATEGORY_IDS,
} from '@features/transactions/constants/categoriesIcons'
import { changeCategory, selectCategoryByTransactionId } from '@features/transactions/store'
import { ArrowBackOutlined } from '@mui/icons-material'
import {
  Box,
  Button,
  IconButton,
  MenuItem,
  Select,
  Stack,
  SvgIconTypeMap,
  Typography,
} from '@mui/material'
import { OverridableComponent } from '@mui/material/OverridableComponent'
import { useTranslate } from '@shared/hooks'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { useNavigate, useParams } from 'react-router'

const ChangeCategory = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions.Modal.ChangeCategory')
  const translateCategory = useTranslate('Categories')

  const { id: transactionId } = useParams()
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
    navigate(-1)
  }

  const renderCategory = (
    value: number,
    // eslint-disable-next-line @typescript-eslint/no-empty-object-type
    Icon: LazyExoticComponent<OverridableComponent<SvgIconTypeMap<{}, 'svg'>>>,
  ) => {
    return (
      <Stack direction="row" spacing={1} alignItems="center">
        <Suspense fallback={<Box width={16} height={16} />}>
          <Icon fontSize="small" />
        </Suspense>

        <Typography>{translateCategory(value)}</Typography>
      </Stack>
    )
  }

  return (
    <>
      <IconButton
        onClick={() => navigate(-1)}
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

            return renderCategory(value, Icon)
          }}
        >
          {availableCategories.map((categoryId) => {
            const Icon = CATEGORIES_ICONS_MAP.get(categoryId)!
            return (
              <MenuItem key={categoryId} value={String(categoryId)}>
                {renderCategory(categoryId, Icon)}
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
    </>
  )
}

export default ChangeCategory
