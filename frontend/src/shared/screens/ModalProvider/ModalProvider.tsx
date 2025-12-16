import { MODALS_MAP } from '@shared/constants/modals'
import { useAppDispatch, useAppSelector } from '@shared/store'
import { closeModal } from '@shared/store/modal'

export function ModalProvider() {
  const dispatch = useAppDispatch()
  const { id, props } = useAppSelector((s) => s.modal)

  if (!id) return null

  const handleClose = () => {
    dispatch(closeModal())
  }

  const ModalComponent = MODALS_MAP[id]

  if (!ModalComponent) return null

  return <ModalComponent {...props} onClose={handleClose} />
}
