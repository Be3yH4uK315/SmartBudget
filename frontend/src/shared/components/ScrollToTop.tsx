import { KeyboardArrowUp } from '@mui/icons-material'
import { Box, Fab, useScrollTrigger, Zoom } from '@mui/material'

export const ScrollToTop = () => {
  const isScrolled = useScrollTrigger({ disableHysteresis: true })

  const handleClick = () => {
    const anchor = document.querySelector('#back-to-top-anchor')
    if (!anchor) return

    anchor.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  return (
    <Zoom in={isScrolled}>
      <Box
        onClick={handleClick}
        role="presentation"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
      >
        <Fab
          sx={{
            color: 'text.main',
            backgroundColor: 'primary.main',
            boxShadow: 10,
            ':hover': { backgroundColor: 'surface.light', color: 'primary.dark' },
          }}
          size="large"
        >
          <KeyboardArrowUp fontSize="large" />
        </Fab>
      </Box>
    </Zoom>
  )
}
