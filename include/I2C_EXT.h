#ifndef I2C_EXT_h
#define I2C_EXT_h

/**
 * Includes
 */
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>
#include "TCA9548.h"

/**
 * AD5934 Library class
 *  Contains mainly functions for interfacing with the AD5934.
 */
class AD5934
{
    public:
        //setup AD5934 sequence
        bool setupAD5934( unsigned long startFrequency);


        // Reset the board
        static bool reset(void);

        // Clock configuration
        static bool setExternalClock(void);  // Added this to explicitly set external clockclock option.
        bool setSettlingCycles(int);

        // Frequency sweep configuration
        static bool setStartFrequency(unsigned long);
        static bool setIncrementFrequency(unsigned long);
        static bool setNumberIncrements(unsigned int);

        // Gain configuration
        static bool setPGAGain(byte);

        // Excitation range configuration
        bool setRange(byte);

        // Read registers
        static byte readRegister(byte);
        static byte readStatusRegister(void);
        static int readControlRegister(void);

        // Impedance data
        static bool getComplexData(int*, int*);

        // Set control mode register (CTRL_REG1)
        static bool setControlMode(byte);

        // Power mode
        static bool setPowerMode(byte);

        // Perform frequency sweeps
        static bool frequencySweep(int real[], int imag[], int);
        static bool calibrate(double gain[], int phase[], int ref, int n);
        static bool calibrate(double gain[], int phase[], int real[],
                              int imag[], int ref, int n);
    private:

        // Sending/Receiving byte method, for easy re-use
        static int getByte(byte, byte*);
        static bool sendByte(byte, byte);
};


/**
 * AD5934 Register Map
 *  Datasheet p20
 */
// Device address and address pointer p20
#define AD5934_ADDR     (0x0D)
#define ADDR_PTR        (0xB0)
// Control Register
#define CTRL_REG1       (0x80)
#define CTRL_REG2       (0x81)
// Start Frequency Register
#define START_FREQ_1    (0x82)
#define START_FREQ_2    (0x83)
#define START_FREQ_3    (0x84)
// Frequency increment register
#define INC_FREQ_1      (0x85)
#define INC_FREQ_2      (0x86)
#define INC_FREQ_3      (0x87)
// Number of increments register
#define NUM_INC_1       (0x88)
#define NUM_INC_2       (0x89)
// Number of settling time cycles register
#define NUM_SCYCLES_1   (0x8A)
#define NUM_SCYCLES_2   (0x8B)
// Status register
#define STATUS_REG      (0x8F)
// Real data register
#define REAL_DATA_1     (0x94)
#define REAL_DATA_2     (0x95)
// Imaginary data register
#define IMAG_DATA_1     (0x96)
#define IMAG_DATA_2     (0x97)

/**
 * Constants
 *  Constants for use with the AD5934 library class.
 */
// Clock sources
#define CLOCK_EXTERNAL  (CTRL_CLOCK_EXTERNAL)
// PGA gain options
#define PGA_GAIN_X1     (CTRL_PGA_GAIN_X1)
#define PGA_GAIN_X5     (CTRL_PGA_GAIN_X5)
// Power modes
#define POWER_STANDBY   (CTRL_STANDBY_MODE)
#define POWER_DOWN      (CTRL_POWER_DOWN_MODE)
#define POWER_ON        (CTRL_NO_OPERATION)
// I2C result success/fail
#define I2C_RESULT_SUCCESS       (0)
#define I2C_RESULT_DATA_TOO_LONG (1)
#define I2C_RESULT_ADDR_NAK      (2)
#define I2C_RESULT_DATA_NAK      (3)
#define I2C_RESULT_OTHER_FAIL    (4)
// Control output voltage range options p20
#define CTRL_OUTPUT_RANGE_1     (0b00000000) //2.0 V p-p typical
#define CTRL_OUTPUT_RANGE_2     (0b00000110) //1.0 V p-p typical
#define CTRL_OUTPUT_RANGE_3     (0b00000010) //200 mV p-p typical
#define CTRL_OUTPUT_RANGE_4     (0b00000100) //400 mV p-p typical
// Control register options
#define CTRL_NO_OPERATION       (0b00000000)
#define CTRL_INIT_START_FREQ    (0b00010000)
#define CTRL_START_FREQ_SWEEP   (0b00100000)
#define CTRL_INCREMENT_FREQ     (0b00110000)
#define CTRL_REPEAT_FREQ        (0b01000000)
#define CTRL_POWER_DOWN_MODE    (0b10100000)
#define CTRL_STANDBY_MODE       (0b10110000)
#define CTRL_RESET              (0b00010000)
#define CTRL_CLOCK_EXTERNAL     (0b00001000)
#define CTRL_PGA_GAIN_X1        (0b00000001)
#define CTRL_PGA_GAIN_X5        (0b00000000)
// Status register options
#define STATUS_DATA_VALID       (0x02) //Valid real/imaginary data p22
#define STATUS_SWEEP_DONE       (0x04) //Frequency sweep complete p22
#define STATUS_ERROR            (0xFF)
// Frequency sweep parameters
#define SWEEP_DELAY             (1)

#define START_FREQUENCY1 14234 //microcantilever specific resonant frequency minus half of the number of increments
#define START_FREQUENCY2 16580 //microcantilever specific resonant frequency minus half of the number of increments
#define START_FREQUENCY3 15310 //microcantilever specific resonant frequency minus half of the number of increments

#define NUM_INCREMENTS  501
#define STEP_SIZE 1 //increment frequency (1)
#define SETTLING_CYCLES 10 // Define the settling cycles (adjust as needed)


void SweepAndProcess(uint8_t channel, AD5934 &device, TCA9548 &multiplexer, 
                     float magnitudeData[][NUM_INCREMENTS], float phaseData[][NUM_INCREMENTS], int deviceIndex);


// BME680 initialization
bool setupBME680(Adafruit_BME680 &bme);

#endif

