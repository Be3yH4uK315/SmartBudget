import { type MouseEvent, useState } from 'react'
import { KeyboardArrowDownOutlined } from '@mui/icons-material'
import { Box, Menu, MenuItem, Stack, Typography } from '@mui/material'
import EnIcon from '@shared/assets/en.svg'
import RuIcon from '@shared/assets/ru.svg'
import { useLocalization } from '@shared/hooks'
import { Languages } from '@shared/types'

export const LanguageMenu = () => {
  const { language, changeLanguage } = useLocalization()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleChoice = (chosenLanguage: Languages) => () => {
    changeLanguage(chosenLanguage)
    handleClose()
  }

  const handleClick = (event: MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  return (
    <>
      <Stack
        direction="row"
        onClick={handleClick}
        spacing={1}
        sx={{
          alignItems: 'center',
          cursor: 'pointer',
          backgroundColor: 'surface.light',
          borderRadius: 1,
          padding: '12px',
        }}
      >
        <Box
          component="img"
          src={languageToIcon[language]}
          sx={{ width: '22px', height: '14px' }}
        />

        <KeyboardArrowDownOutlined sx={{ color: 'gray.main', transition: 'all 150ms' }} />
      </Stack>

      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleClose}>
        <MenuItem onClick={handleChoice('ru')} selected={language === 'ru'}>
          <Box
            component="img"
            src={RuIcon}
            sx={{ width: '30px', height: '15px', marginRight: '4px' }}
          />

          <Typography>Русский</Typography>
        </MenuItem>

        <MenuItem onClick={handleChoice('en')} selected={language === 'en'}>
          <Box
            component="img"
            src={EnIcon}
            sx={{ width: '30px', height: '15px', marginRight: '4px' }}
          />

          <Typography>English</Typography>
        </MenuItem>
      </Menu>
    </>
  )
}

const languageToIcon: Record<Languages, any> = {
  en: EnIcon,
  ru: RuIcon,
}
