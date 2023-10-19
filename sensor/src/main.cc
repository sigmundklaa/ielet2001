
#include "data.hh"
#include <Wire.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Adafruit_sensor.h>
#include <Adafruit_BME280.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Arduino.h>

/* BME280 */

Adafruit_BME280 bme

int* bme280()
{
    status = bme.begin(0x76); /* 0x76 is the address for the BME280 sensor 
                                 on the I2C bus. If this doesn't work you 
                                 need to find the correct one. */

    if (!status) {
        Serial.println("An error occured trying to find the BME280 sensor, trying again...");
	    while (!status) {
	        status = bme.begin(0x76);
            delay(1000);
            }
	    Serial.println("BME280 sensor is connected, resuming...")
    }

    return {bme.readTemperature(), bme.readHumidity(), bme.readPressure()}
    
}

/* DS18B20 */

const int oneWireBus = 4 //(example GPIO pin)
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

float DS18B20()
{
    sensors.requestTemperatures(); 
    return sensors.getTempCByIndex(0)
}

/* Wind sensors */

const int windDirectionPin = 35; //example GPIO pins
const int windSpeedPin = 14;


/* Put ESP32 in deep sleep mode */

void sleep() 
{
    esp_wifi_stop();
    esp_sleep_enable_timer_wakeup(3600000000); //microseconds (3 600 000 000 equals 1 hour)
    esp_deep_sleep_start();
}

void setup()
{
    Serial.begin(115200);

    ++bootCount;
    Serial.println("Boot number: " + String(bootCount));

    WiFi.mode(WIFI_STA); //for espNOW

    sensors.begin(); //DS18B20
    
    uint8_t buf[256];
    sensor_data data;
    data::encode(data, buf, sizeof(buf));
}

void loop() {}