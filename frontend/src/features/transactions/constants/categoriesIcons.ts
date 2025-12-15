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
  [0, StorefrontOutlined],
  [1, FastfoodOutlined],
  [2, CheckroomOutlined],
  [3, BlenderOutlined],
  [4, ConstructionOutlined],
  [5, KingBedOutlined],
  [6, SpaOutlined],
  [7, PetsOutlined],
  [8, AutoStoriesOutlined],
  [9, VaccinesOutlined],
  [10, MedicalInformationOutlined],
  [11, LocalGasStationOutlined],
  [12, BuildOutlined],
  [13, SettingsOutlined],
  [14, LocalParkingOutlined],
  [15, CloudDoneOutlined],
  [16, SportsEsportsOutlined],
  [17, ShoppingCartOutlined],
  [18, DirectionsBusOutlined],
  [19, LocalTaxiOutlined],
  [20, RealEstateAgentOutlined],
  [21, RouterOutlined],
  [22, SavingsOutlined],
  [23, SchoolOutlined],
  [24, LocalActivityOutlined],
  [25, FitnessCenterOutlined],
  [26, AirplanemodeActiveOutlined],
  [27, AutoAwesomeOutlined],
  [28, LocalFlorist],
  [29, ShoppingBagOutlined],
])

export const CATEGORY_IDS = Array.from(CATEGORIES_ICONS_MAP.keys())
