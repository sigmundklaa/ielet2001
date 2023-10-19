
#include "data.hh"
#include <Wire.h>
#include <WiFi.h>
#include <esp_now.h>
#include <Adafruit_sensor.h>
#include <Adafruit_BME280.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Arduino.h>

void setup()
{

    uint8_t buf[256];
    sensor_data data;
    data::encode(data, buf, sizeof(buf));
}

void loop() {}