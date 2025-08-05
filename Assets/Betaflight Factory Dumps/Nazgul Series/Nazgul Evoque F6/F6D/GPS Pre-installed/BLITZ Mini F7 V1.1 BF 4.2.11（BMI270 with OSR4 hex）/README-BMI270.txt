2022 March 17: XING

This is our iFlight custom target based on Betaflight 4.2.11 including:

+ BMI270 gyro driver
+ DPS310 Barometer driver
+ BMI270 OSR4 oversampling mode enabled by default (hardware Lowpass at 300hz, more noise resistant, performance similar to MPU6000)

All provided files have been tested and are fully functional with all iFlight flight controllers using that specific target.
Works with BMI270 as well as MPU6000 gyros.

!!PLEASE FLASH WITH CARE and always test a new configuration in confined area!!
iFlight is not responsible for inproper use or lost gear!

= Why do we have to use custom files?
At this point in time only beta and release canidates of Betaflight 4.3 support the new BMI270 gyro and the DPS310 barometer.
We wanted to provide a stable release firmware for our iFlight customers that don't want to use 4.3 just yet.
The official 4.2.11 downloaded and flashed through the Configurator does NOT recognize the BMI270 or DPS310 originally.

= Why do newer FCs come with a Bosch GMI270 gyro instead of the MPU6000?
Due to chip shortages and high prices we were forced to switch the gyro.

= Why do newer FCs come with a DPS310 Barometer instead of the BMP280?
The DPS310 offers a higher accuracy, as well as sourcing issues with the BMP280.

= How to flash:
1. Make sure you're using the Betaflight Configurator 10.7.2 for 4.2.x firmwares.
2. Select "Update Firmware" on the upper right in your Betaflight Configurator.
3. Click on "Load Firmware (Local) on the bottom right and select the custom hex
4. Make sure the right hex file is selected for your iFlight FC.
5. Flash firmware.

The source code is published here: https://github.com/Guidus93/betaflight/tree/4.2.11-BMI
OSR4 Pull request and further details: https://github.com/betaflight/betaflight/pull/11400
