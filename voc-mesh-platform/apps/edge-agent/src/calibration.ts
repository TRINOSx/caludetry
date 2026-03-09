export interface RawReading {
  compound: string;
  value_ppm: number;
  raw_adc: number;
}

export interface CalibratedReading {
  compound: string;
  value_ppm: number;
  raw_adc: number;
  corrected_adc: number;
  corrected_ppm: number;
}

const TEMP_COEFF_A = -0.012501;
const TEMP_COEFF_B = 1.35347167;

const PPM_COEFF_A = 2.92395047;
const PPM_COEFF_B = 0.02952922;
const PPM_COEFF_C = 0.43941621;

/**
 * Apply temperature compensation to a raw ADC value.
 * Formula: rawAdc * (a * tempC + b)
 * where a = -0.012501, b = 1.35347167
 */
export function temperatureCompensation(rawAdc: number, tempC: number): number {
  return rawAdc * (TEMP_COEFF_A * tempC + TEMP_COEFF_B);
}

/**
 * Convert a temperature-corrected ADC value to PPM.
 * Formula: a * (1 - b * correctedValue) + c
 * where a = 2.92395047, b = 0.02952922, c = 0.43941621
 */
export function ppmConversion(correctedValue: number): number {
  return PPM_COEFF_A * (1 - PPM_COEFF_B * correctedValue) + PPM_COEFF_C;
}

/**
 * Calibrate an array of raw readings using temperature compensation
 * and PPM conversion.
 */
export function calibrateReadings(
  readings: RawReading[],
  tempC: number
): CalibratedReading[] {
  return readings.map((reading) => {
    const correctedAdc = temperatureCompensation(reading.raw_adc, tempC);
    const correctedPpm = ppmConversion(correctedAdc);

    return {
      compound: reading.compound,
      value_ppm: reading.value_ppm,
      raw_adc: reading.raw_adc,
      corrected_adc: correctedAdc,
      corrected_ppm: correctedPpm,
    };
  });
}
