export type CompoundCategory =
  | "stress"
  | "defense"
  | "flowering"
  | "atmosphere"
  | "soil_gas"
  | "industrial";

export interface VOCCompound {
  id: string;
  name: string;
  formula: string;
  category: CompoundCategory;
  unit: string;
}

export const VOC_COMPOUNDS: VOCCompound[] = [
  { id: "ethylene", name: "Ethylene", formula: "C2H4", category: "stress", unit: "ppm" },
  { id: "ethanol", name: "Ethanol", formula: "C2H5OH", category: "stress", unit: "ppm" },
  { id: "methane", name: "Methane", formula: "CH4", category: "soil_gas", unit: "ppm" },
  { id: "ammonia", name: "Ammonia", formula: "NH3", category: "soil_gas", unit: "ppm" },
  { id: "co2", name: "Carbon Dioxide", formula: "CO2", category: "atmosphere", unit: "ppm" },
  { id: "co", name: "Carbon Monoxide", formula: "CO", category: "atmosphere", unit: "ppm" },
  { id: "h2", name: "Hydrogen", formula: "H2", category: "soil_gas", unit: "ppm" },
  { id: "formaldehyde", name: "Formaldehyde", formula: "CH2O", category: "industrial", unit: "ppb" },
  { id: "ozone", name: "Ozone", formula: "O3", category: "atmosphere", unit: "ppb" },
  { id: "h2s", name: "Hydrogen Sulfide", formula: "H2S", category: "soil_gas", unit: "ppb" },
  { id: "isoprene", name: "Isoprene", formula: "C5H8", category: "stress", unit: "ppb" },
  { id: "alpha_pinene", name: "alpha-Pinene", formula: "C10H16", category: "defense", unit: "ppb" },
  { id: "beta_pinene", name: "beta-Pinene", formula: "C10H16", category: "defense", unit: "ppb" },
  { id: "limonene", name: "Limonene", formula: "C10H16", category: "defense", unit: "ppb" },
  { id: "linalool", name: "Linalool", formula: "C10H18O", category: "flowering", unit: "ppb" },
  { id: "methyl_salicylate", name: "Methyl Salicylate", formula: "C8H8O3", category: "defense", unit: "ppb" },
  { id: "methyl_jasmonate", name: "Methyl Jasmonate", formula: "C13H20O3", category: "defense", unit: "ppb" },
  { id: "cis_3_hexenal", name: "cis-3-Hexenal", formula: "C6H10O", category: "stress", unit: "ppb" },
  { id: "hexanal", name: "Hexanal", formula: "C6H12O", category: "stress", unit: "ppb" },
  { id: "nonanal", name: "Nonanal", formula: "C9H18O", category: "stress", unit: "ppb" },
  { id: "tvoc", name: "Total VOC", formula: "TVOC", category: "atmosphere", unit: "ppb" },
  { id: "voc", name: "VOC (generic)", formula: "VOC", category: "atmosphere", unit: "ppb" },
  { id: "benzene", name: "Benzene", formula: "C6H6", category: "industrial", unit: "ppb" },
  { id: "toluene", name: "Toluene", formula: "C7H8", category: "industrial", unit: "ppb" },
  { id: "xylene", name: "Xylene", formula: "C8H10", category: "industrial", unit: "ppb" },
  { id: "styrene", name: "Styrene", formula: "C8H8", category: "industrial", unit: "ppb" },
  { id: "acetone", name: "Acetone", formula: "C3H6O", category: "stress", unit: "ppb" },
  { id: "acetaldehyde", name: "Acetaldehyde", formula: "C2H4O", category: "stress", unit: "ppb" },
  { id: "no2", name: "Nitrogen Dioxide", formula: "NO2", category: "atmosphere", unit: "ppb" },
  { id: "so2", name: "Sulfur Dioxide", formula: "SO2", category: "atmosphere", unit: "ppb" },
  { id: "butadiene", name: "1,3-Butadiene", formula: "C4H6", category: "industrial", unit: "ppb" },
  { id: "carbon_disulfide", name: "Carbon Disulfide", formula: "CS2", category: "soil_gas", unit: "ppb" },
  { id: "dimethyl_disulfide", name: "Dimethyl Disulfide", formula: "C2H6S2", category: "soil_gas", unit: "ppb" },
  { id: "methanol", name: "Methanol", formula: "CH3OH", category: "stress", unit: "ppm" },
  { id: "trimethylamine", name: "Trimethylamine", formula: "C3H9N", category: "soil_gas", unit: "ppb" },
  { id: "indole", name: "Indole", formula: "C8H7N", category: "flowering", unit: "ppb" },
  { id: "geraniol", name: "Geraniol", formula: "C10H18O", category: "flowering", unit: "ppb" },
  { id: "myrcene", name: "Myrcene", formula: "C10H16", category: "defense", unit: "ppb" },
  { id: "ocimene", name: "Ocimene", formula: "C10H16", category: "defense", unit: "ppb" },
  { id: "farnesene", name: "Farnesene", formula: "C15H24", category: "defense", unit: "ppb" },
  { id: "beta_caryophyllene", name: "beta-Caryophyllene", formula: "C15H24", category: "defense", unit: "ppb" },
  { id: "dmnt", name: "DMNT", formula: "C11H18", category: "defense", unit: "ppb" },
  { id: "tmtt", name: "TMTT", formula: "C16H26", category: "defense", unit: "ppb" },
  { id: "acetic_acid", name: "Acetic Acid", formula: "C2H4O2", category: "stress", unit: "ppb" },
  { id: "formic_acid", name: "Formic Acid", formula: "CH2O2", category: "stress", unit: "ppb" },
  { id: "propane", name: "Propane", formula: "C3H8", category: "industrial", unit: "ppm" },
  { id: "butane", name: "Butane", formula: "C4H10", category: "industrial", unit: "ppm" },
  { id: "pm25", name: "PM2.5", formula: "PM2.5", category: "atmosphere", unit: "ug/m3" },
  { id: "pm10", name: "PM10", formula: "PM10", category: "atmosphere", unit: "ug/m3" },
  { id: "sgp40_index", name: "SGP40 VOC Index", formula: "SGP40", category: "atmosphere", unit: "index" },
];
