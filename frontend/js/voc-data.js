/* ================================
   VOC Compound Database
   Bosch Nose - 300+ VOC Compounds
   ================================ */

const VOC_COMPOUNDS = {
    // Primary gases (dashboard display)
    primary: [
        { id: 'oxygen_gen', name: 'Oxygen Generate', unit: 'T/HR', value: 500, color: '#10b981' },
        { id: 'co2_trans', name: 'CO2 Transformate', unit: 'T/HR', value: 200, color: '#22c55e' },
        { id: 'hydrogen', name: 'Hydrogen', formula: 'H2', unit: 'PPB', value: 300, color: '#f59e0b' },
        { id: 'methane', name: 'Methane', formula: 'CH4', unit: 'ppb', value: 400, color: '#10b981' },
        { id: 'ammonia', name: 'Ammonia', formula: 'NH3', unit: 'ppb', value: 400, color: '#f97316' },
        { id: 'ethanolol', name: 'Etanethanol', formula: 'EtOH', unit: 'ppb', value: 400, color: '#8b5cf6' },
        { id: 'formaldehyde', name: 'Formaldehyde', formula: 'HCHO', unit: 'PPB', value: 400, color: '#ef4444' },
        { id: 'co_monoxide', name: 'Carbon Monoxide', formula: 'CO', unit: 'PPB', value: 400, color: '#dc2626' },
        { id: 'co2', name: 'Carbon Dioxide', formula: 'CO2', unit: 'PPB', value: 400, color: '#22c55e' },
        { id: 'no2', name: 'Nitrogen Dioxide', formula: 'NO2', unit: 'PPB', value: 400, color: '#3b82f6' },
        { id: 'ozone', name: 'Ozone', formula: 'O3', unit: 'PPB', value: 400, color: '#06b6d4' },
        { id: 'sulfur', name: 'Sulfur', formula: 'S', unit: 'PPB', value: 400, color: '#eab308' },
    ],

    // Full Bosch Nose VOC list
    boschNose: [
        { formula: 'VOC', name: 'VOC' },
        { formula: 'VOC2', name: 'VOC2' },
        { formula: 'TVOC', name: 'TVOC' },
        { formula: 'TVOC2', name: 'TVOC2' },
        { formula: 'CO', name: 'Carbon monoxide' },
        { formula: 'CO2', name: 'Carbon dioxide' },
        { formula: 'NO2', name: 'Nitrogen dioxide' },
        { formula: 'C2H5OH', name: 'Ethanol' },
        { formula: 'H2', name: 'Hydrogen' },
        { formula: 'NH3', name: 'Ammonia' },
        { formula: 'CH4', name: 'Methane' },
        { formula: 'CH3COOH', name: 'Acetic acid' },
        { formula: 'C2H2', name: 'Acetylene' },
        { formula: 'C3H3N', name: 'Acrylonitrile' },
        { formula: 'C6H6', name: 'Benzene' },
        { formula: 'C4H6', name: 'Butadiene' },
        { formula: 'CS2', name: 'Carbon disulfide' },
        { formula: 'C2H6S2', name: 'Dimethyl Disulfide' },
        { formula: 'C2H4', name: 'Ethylene' },
        { formula: 'C2H4O', name: 'Ethylene oxide' },
        { formula: 'HCHO', name: 'Formaldehyde' },
        { formula: 'HCOOH', name: 'Formic acid' },
        { formula: 'HCl', name: 'Hydrogen chloride' },
        { formula: 'HCN', name: 'Hydrogen cyanide' },
        { formula: 'C4H8', name: 'Isobutene' },
        { formula: 'CH3OH', name: 'Methanol' },
        { formula: 'CH4S', name: 'Methyl mercaptan' },
        { formula: 'C2H6S', name: 'Methyl sulfide' },
        { formula: 'C8H10', name: 'O-xylene' },
        { formula: 'C8H8', name: 'Styrene' },
        { formula: 'C7H8', name: 'Toluene' },
        { formula: 'C3H6N', name: 'Trimethylamine' },
        { formula: 'H2S', name: 'Hydrogen sulfide' },
        { formula: 'EtOH', name: 'Ethanol' },
        { formula: 'C3H8', name: 'Propane' },
        { formula: 'C4H10', name: 'Iso-butane' },
        { formula: 'O3', name: 'Ozone' },
    ],

    // Extended compound list (ML ready)
    extended: [
        { formula: 'C12H8', name: 'Acenaphthalene' },
        { formula: 'C12H10', name: 'Acenaphthene' },
        { formula: 'C2H4O2', name: 'Acetaldehyde' },
        { formula: 'C2H5NO', name: 'Acetamide' },
        { formula: 'C4H6O3', name: 'Acetic anhydride' },
        { formula: 'C4H8O2', name: 'Acetoin' },
        { formula: 'C3H6O', name: 'Acetone' },
        { formula: 'C8H8O', name: 'Acetophenone' },
        { formula: 'C2H3BrO', name: 'Acetyl bromide' },
        { formula: 'C3H4O', name: 'Acrylic acid' },
        { formula: 'C3H6O2', name: 'Allyl alcohol' },
        { formula: 'C3H5Br', name: 'Allyl bromide' },
        { formula: 'C3H5Cl', name: 'Allyl chloride' },
        { formula: 'C5H10O2', name: 'Amyl acetate' },
        { formula: 'C6H7N', name: 'Aniline' },
        { formula: 'C7H8O', name: 'Anisole' },
        { formula: 'C7H6O', name: 'Benzaldehyde' },
        { formula: 'C7H6O2', name: 'Benzoic acid' },
        { formula: 'C9H10O2', name: 'Benzyl acetate' },
        { formula: 'C7H8O2', name: 'Benzyl alcohol' },
        { formula: 'C7H7Cl', name: 'Benzyl chloride' },
        { formula: 'C12H10', name: 'Biphenyl' },
        { formula: 'CHBr3', name: 'Bromoform' },
        { formula: 'C4H10', name: 'Butane' },
        { formula: 'C4H10O', name: '1-Butanol' },
        { formula: 'C4H10O2', name: '2-Butanol' },
        { formula: 'C4H8O', name: 'Butanone (MEK)' },
        { formula: 'C4H8', name: '1-Butene' },
        { formula: 'C6H12O2', name: 'Butyl acetate' },
        { formula: 'C7H12O2', name: 'Butyl acrylate' },
        { formula: 'C4H11N', name: 'n-Butylamine' },
        { formula: 'C4H8O2', name: 'Butylene oxide' },
        { formula: 'C4H8O3', name: 'Butyraldehyde' },
        { formula: 'C4H8O4', name: 'Butyric acid' },
        { formula: 'C10H16O', name: 'Camphor' },
        { formula: 'C10H14O', name: 'Carvone' },
        { formula: 'C6H5Cl', name: 'Chlorobenzene' },
        { formula: 'C4H9Cl', name: '1-Chlorobutane' },
        { formula: 'C2H5Cl', name: 'Chloroethane' },
        { formula: 'C2H5ClO', name: '2-Chloroethanol' },
        { formula: 'CHCl3', name: 'Chloroform' },
        { formula: 'C7H7Cl2', name: 'Chlorotoluene' },
        { formula: 'C7H8O3', name: 'Cresol' },
        { formula: 'C4H6O', name: 'Crotonaldehyde' },
        { formula: 'C9H12', name: 'Cumene' },
        { formula: 'C6H12', name: 'Cyclohexane' },
        { formula: 'C6H12O', name: 'Cyclohexanol' },
        { formula: 'C6H10O', name: 'Cyclohexanone' },
        { formula: 'C6H10', name: 'Cyclohexene' },
        { formula: 'C5H10', name: 'Cyclopentane' },
        { formula: 'C5H8O', name: 'Cyclopentanone' },
        { formula: 'C5H8', name: 'Cyclopentene' },
        { formula: 'C10H22', name: 'Decane' },
        { formula: 'C2H4Br2', name: '1,2-Dibromoethane' },
        { formula: 'C6H4Cl2', name: 'o-Dichlorobenzene' },
        { formula: 'C2H4Cl2', name: '1,1-Dichloroethane' },
        { formula: 'C2H2Cl2', name: '1,1-Dichloroethene' },
        { formula: 'CH2Cl2', name: 'Dichloromethane' },
        { formula: 'C10H12', name: 'Dicyclopentadiene' },
        { formula: 'C4H10O', name: 'Diethyl ether' },
        { formula: 'C4H10S', name: 'Diethyl sulfide' },
        { formula: 'C4H11N2', name: 'Diethylamine' },
        { formula: 'C8H16', name: 'Diisobutylene' },
        { formula: 'C6H14O', name: 'Diisopropyl ether' },
        { formula: 'C3H8O2', name: 'Dimethoxymethane' },
        { formula: 'C2H6O', name: 'Dimethyl ether' },
        { formula: 'C2H6OS', name: 'Dimethyl sulfoxide' },
        { formula: 'C4H9NO', name: 'Dimethylacetamide' },
        { formula: 'C2H7N', name: 'Dimethylamine' },
        { formula: 'C8H11N', name: 'Dimethylaniline' },
        { formula: 'C3H7NO', name: 'Dimethylformamide' },
        { formula: 'C2H8N2', name: 'Dimethylhydrazine' },
        { formula: 'C4H8O2_d', name: '1,4-Dioxane' },
        { formula: 'C3H5ClO', name: 'Epichlorohydrin' },
        { formula: 'C2H6', name: 'Ethane' },
        { formula: 'C4H8O2_ea', name: 'Ethyl acetate' },
        { formula: 'C5H8O2', name: 'Ethyl acrylate' },
    ],

    // Agricultural VOC signatures (plant metabolism)
    agricultural: [
        { name: 'Isoprene', formula: 'C5H8', significance: 'Plant stress indicator' },
        { name: 'Alpha-pinene', formula: 'C10H16', significance: 'Terpene - defense mechanism' },
        { name: 'Beta-pinene', formula: 'C10H16', significance: 'Terpene - defense mechanism' },
        { name: 'Limonene', formula: 'C10H16', significance: 'Terpene - pest defense' },
        { name: 'Linalool', formula: 'C10H18O', significance: 'Floral - pollination signal' },
        { name: 'Methyl salicylate', formula: 'C8H8O3', significance: 'Defense signal (SAR)' },
        { name: 'Methyl jasmonate', formula: 'C13H20O3', significance: 'Wound/herbivore signal' },
        { name: 'cis-3-Hexenal', formula: 'C6H10O', significance: 'Green leaf volatile - damage' },
        { name: 'trans-2-Hexenal', formula: 'C6H10O', significance: 'Green leaf volatile - damage' },
        { name: 'Hexanal', formula: 'C6H12O', significance: 'Lipid oxidation - stress' },
        { name: 'Nonanal', formula: 'C9H18O', significance: 'Lipid peroxidation' },
        { name: 'Decanal', formula: 'C10H20O', significance: 'Oxidative stress' },
        { name: 'Beta-caryophyllene', formula: 'C15H24', significance: 'Below-ground defense' },
        { name: 'DMNT', formula: 'C11H18', significance: 'Herbivore-induced signal' },
        { name: 'TMTT', formula: 'C16H26', significance: 'Spider mite defense signal' },
        { name: 'Indole', formula: 'C8H7N', significance: 'Nocturnal defense / priming' },
        { name: 'Geraniol', formula: 'C10H18O', significance: 'Floral VOC / pollinator' },
        { name: 'Myrcene', formula: 'C10H16', significance: 'Monoterpene - stress' },
        { name: 'Ocimene', formula: 'C10H16', significance: 'Herbivore defense signal' },
        { name: 'Farnesene', formula: 'C15H24', significance: 'Aphid alarm pheromone mimic' },
    ],
};

// Generate simulated VOC values
function generateVOCValues() {
    const values = {};
    const allCompounds = [
        ...VOC_COMPOUNDS.boschNose,
        ...VOC_COMPOUNDS.extended,
        ...VOC_COMPOUNDS.agricultural,
    ];

    allCompounds.forEach(compound => {
        const key = compound.formula || compound.id || compound.name;
        values[key] = {
            value: Math.round(Math.random() * 500 + 10),
            unit: 'ppb',
            name: compound.name,
            formula: compound.formula,
            significance: compound.significance || null,
            timestamp: new Date().toISOString(),
        };
    });

    return values;
}

// Get VOC status level
function getVOCLevel(value, compound) {
    const thresholds = CONFIG.THRESHOLDS[compound] || { low: 100, normal: 300, elevated: 500, high: 800 };
    if (value <= thresholds.low) return 'low';
    if (value <= thresholds.normal) return 'normal';
    if (value <= thresholds.elevated) return 'elevated';
    return 'high';
}

// ML Feature Vector (300+ dimensions)
function generateVOCVector() {
    const allCompounds = [
        ...VOC_COMPOUNDS.boschNose,
        ...VOC_COMPOUNDS.extended,
        ...VOC_COMPOUNDS.agricultural,
    ];

    return allCompounds.map(() => parseFloat((Math.random()).toFixed(4)));
}
