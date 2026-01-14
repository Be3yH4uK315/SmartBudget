import AirplanemodeActiveOutlined from '@mui/icons-material/AirplanemodeActiveOutlined'
import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import AutoStoriesOutlined from '@mui/icons-material/AutoStoriesOutlined'
import BlenderOutlined from '@mui/icons-material/BlenderOutlined'
import BuildOutlined from '@mui/icons-material/BuildOutlined'
import CheckroomOutlined from '@mui/icons-material/CheckroomOutlined'
import CloudDoneOutlined from '@mui/icons-material/CloudDoneOutlined'
import ConstructionOutlined from '@mui/icons-material/ConstructionOutlined'
import DirectionsBusOutlined from '@mui/icons-material/DirectionsBusOutlined'
import FastfoodOutlined from '@mui/icons-material/FastfoodOutlined'
import FitnessCenterOutlined from '@mui/icons-material/FitnessCenterOutlined'
import KingBedOutlined from '@mui/icons-material/KingBedOutlined'
import LocalActivityOutlined from '@mui/icons-material/LocalActivityOutlined'
import LocalFlorist from '@mui/icons-material/LocalFlorist'
import LocalGasStationOutlined from '@mui/icons-material/LocalGasStationOutlined'
import LocalParkingOutlined from '@mui/icons-material/LocalParkingOutlined'
import LocalTaxiOutlined from '@mui/icons-material/LocalTaxiOutlined'
import MedicalInformationOutlined from '@mui/icons-material/MedicalInformationOutlined'
import PetsOutlined from '@mui/icons-material/PetsOutlined'
import RealEstateAgentOutlined from '@mui/icons-material/RealEstateAgentOutlined'
import RouterOutlined from '@mui/icons-material/RouterOutlined'
import SavingsOutlined from '@mui/icons-material/SavingsOutlined'
import SchoolOutlined from '@mui/icons-material/SchoolOutlined'
import SettingsOutlined from '@mui/icons-material/SettingsOutlined'
import ShoppingBagOutlined from '@mui/icons-material/ShoppingBagOutlined'
import ShoppingCartOutlined from '@mui/icons-material/ShoppingCartOutlined'
import SpaOutlined from '@mui/icons-material/SpaOutlined'
import SportsEsportsOutlined from '@mui/icons-material/SportsEsportsOutlined'
import StorefrontOutlined from '@mui/icons-material/StorefrontOutlined'
import VaccinesOutlined from '@mui/icons-material/VaccinesOutlined'
import { SvgIconTypeMap } from '@mui/material'
import { OverridableComponent } from '@mui/material/OverridableComponent'

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
type IconComponent = OverridableComponent<SvgIconTypeMap<{}, 'svg'>>

export const CATEGORIES_ICONS_MAP = new Map<number, IconComponent>([
  [1, ShoppingBagOutlined],
  [2, StorefrontOutlined],
  [3, FastfoodOutlined],
  [4, CheckroomOutlined],
  [5, BlenderOutlined],
  [6, ConstructionOutlined],
  [7, KingBedOutlined],
  [8, SpaOutlined],
  [9, PetsOutlined],
  [10, AutoStoriesOutlined],
  [11, VaccinesOutlined],
  [12, MedicalInformationOutlined],
  [13, LocalGasStationOutlined],
  [14, BuildOutlined],
  [15, SettingsOutlined],
  [16, LocalParkingOutlined],
  [17, CloudDoneOutlined],
  [18, SportsEsportsOutlined],
  [19, ShoppingCartOutlined],
  [20, DirectionsBusOutlined],
  [21, LocalTaxiOutlined],
  [22, RealEstateAgentOutlined],
  [23, RouterOutlined],
  [24, SavingsOutlined],
  [25, SchoolOutlined],
  [26, LocalActivityOutlined],
  [27, FitnessCenterOutlined],
  [28, AirplanemodeActiveOutlined],
  [29, AutoAwesomeOutlined],
  [30, LocalFlorist],
])

export const CATEGORY_IDS = Array.from(CATEGORIES_ICONS_MAP.keys())
