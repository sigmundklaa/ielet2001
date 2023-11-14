#include <Wire.h>
#include <WiFi.h>
#include <SPI.h>
#include <esp_now.h>
#include <Adafruit_BME280.h>
#include <Adafruit_I2CDevice.h>
#include <Adafruit_Sensor.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <ArduinoJson.h>
#include <Arduino.h>
#include <math.h>
#include "WindDirection.hh"

RTC_DATA_ATTR int bootCount = 0; 
//saved to RTC memory so it doesn't get deleted every reboot

//Recieving esp32 mac address for esp-now
uint8_t broadcastAddress[] = {0xF4, 0x12, 0xFA, 0xDC, 0x3B, 0xA4};

esp_now_peer_info_t peerInfo;


#define SENSOR_AVG_MEASURE_INTERVAL 500
#define DEEPSLEEP_WAKEUP_TIMER 3600000000 //microseconds (3600000000 equals 1 hour)

//Calibration values for BME280 sensor
#define BME280_TEMPERATURE_CALIB 0 
#define BME280_HUMIDITY_CALIB 0
#define BME280_PRESSURE_CALIB 0

/* PINS */
#define BME_SCK 18 //SCL pin
#define BME_MISO 19 //ADR pin
#define BME_MOSI 23 //SDA pin
#define BME_CS 5 //CS pin

#define DS18B20_pin 4 //DS18B20 pin (DQ) used for communication bus

/* TIMERS */
unsigned long time_sensor_last; //time of previous sensor readings from ds and bme
unsigned long boot_time; //time of wakeup

/* SENSOR VALUES */
float bme_temperature;
float bme_humidity;
float bme_pressure;
float ds_temperature;
float wind_speed;

/* ESP_NOW */

//Callback function, runs when data is sent
void OnDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) 
{
  Serial.print("\r\nLast Packet Send Status: ");
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Delivery Success" : "Delivery Fail");
}

//Setup for esp-now, runs once at system startup
void espnow_setup()
{
    WiFi.mode(WIFI_STA);

    //initialize esp-now
    if (esp_now_init() != ESP_OK) {
        Serial.println("Error initializing ESP-NOW, trying again...");
        //if initializing esp-now failed it will try 3 more times before continuing
        for(int i = 0; i<3; i++) { 
                if ((esp_now_init() != ESP_OK) && (i < 2)) {
                    Serial.println("Failed, trying again...");
                    delay(2000);
                } else if ((esp_now_init() != ESP_OK) && (i == 2)) {
                    Serial.println("Failed to initialize, resuming...");
                    break;
                } else {
                    Serial.println("ESP-NOW is initialized, resuming...");
                    break;
                }
        }
    } else {
        Serial.println("ESP-NOW is initialized");
    }

    //callback for when data is sent
    esp_now_register_send_cb(OnDataSent);

    /* CONNECT TO RECIEVING ESP32 */

    //add reciever info
    memcpy(peerInfo.peer_addr, broadcastAddress, 6); 

    //select channel
    peerInfo.channel = 0;

    //encryption true/false
    peerInfo.encrypt = false;

    //connect to reciever
    if (esp_now_add_peer(&peerInfo) != ESP_OK){
        Serial.println("Failed to find reciever");
        //if connecting to the recieving esp32 failed, it will try 3 more times before continuing
        for(int i = 0; i<3; i++) {
                if ((esp_now_add_peer(&peerInfo) != ESP_OK) && (i < 2)) {
                    Serial.println("Failed, trying again...");
                    delay(2000);
                } else if ((esp_now_add_peer(&peerInfo) != ESP_OK) && (i == 2)) {
                    Serial.println("Failed to connect, resuming...");
                    break;
                } else {
                    Serial.println("Reciever is connected, resuming...");
                    break;
                }
        }
    } else {
        Serial.println("Connected to reciever");
    }

    
}



/* BME280 */
Adafruit_BME280 bme(BME_CS); //SPI communication

//Setup for bme280 sensor, runs once on startup
void bme280_connect()
{

    // Connect to the BME280 sensor via SPI 
    bool status = bme.begin(); 

    if (!status) {
        Serial.println("An error occured trying to find the BME280 sensor, trying again...");
	    
        // If BME280 sensor isn't found it will lock the program trying to connect 3 more times
        for(int i = 0; i<3; i++) {
            status = bme.begin();
            
            if ((!status) && (i < 2)) {
                Serial.println("Failed, trying again...");
                delay(2000);
            } else if ((!status) && (i == 2)) {
                Serial.println("Failed to connect, resuming...");
                break;
            } else {
                Serial.println("BME280 sensor is connected, resuming...");
                break;
            }
        }  
    }
}


/* DS18B20 */
OneWire oneWire(DS18B20_pin);
DallasTemperature ds(&oneWire);

//Setup for DS18B20, runs once on setup
float DS18B20()
{
    ds.requestTemperatures(); 
    return ds.getTempCByIndex(0);
}

/* Wind sensor */
const int windDirectionPin = 33;
const int windSpeedPin = 32;

uint16_t currspeed;
uint16_t lastspeed;
uint16_t windcount;

unsigned long time_wind_now;

//Measure windspeed on [pin] for [seconds], runs in loop to gather data
void wind_Speed(int pin, int seconds) 
{
    Serial.print("Measuring windspeed for ");
    Serial.print(seconds);
    Serial.println(" seconds");

    time_wind_now = millis();
    windcount = 0;

    while(millis()-time_wind_now <= seconds*1000) 
    { 
        currspeed = analogRead(pin);

        if((currspeed == 4095) && (!lastspeed)) 
        {
            windcount++;
        }

        lastspeed = currspeed;
    }
    /*  For the amount of time decided by input variable, count how many
        half rounds the anemometer (wind speed gauge) turns. 
    */

    wind_speed = (windcount/(seconds))*(2.0/3.0); 
    /*  The anemometer turns half a round every second if the speed is 2.4 km/h
        This is equal to around 2/3 m/s. We take the average count of half rounds
        per second and times it by 2/3 to get the wind speed in m/s.
    */

    Serial.print("Windspeed is: ");
    Serial.print(wind_speed);
    Serial.println(" m/s");

    return;
}


/* Get average sensor values from BME and DS sensors*/

//Get bme and ds sensor values, runs in loop to gather data
void get_avg_values()
{
    bme_temperature = 0;
    bme_humidity = 0;
    bme_pressure = 0;
    ds_temperature = 0;

    Serial.println("Getting average values from BME280 and DS18B20 sensors");

    for(int i = 0; i<5; i++)
    {
        // Delay so measurements are taken at different times
        while(millis() - time_sensor_last <= SENSOR_AVG_MEASURE_INTERVAL) {}
        bme_temperature += bme.readTemperature();
        bme_humidity += bme.readHumidity();
        bme_pressure += bme.readPressure();
        ds_temperature += DS18B20();

        time_sensor_last = millis();
    }
    /*  The for loop adds the read value to the past value 5 times
        and waits for a bit between each loop to avoid the 
        measurements being taken at almost the exact same time
    */

    // Divide by 5 (number of loops) to get the correct values for the sensors
    bme_temperature /= 5;
    bme_humidity /= 5;
    bme_pressure /= 5;
    ds_temperature /= 5;
    
    // Add the calibration offset to get correct BME280 values
    bme_temperature += BME280_TEMPERATURE_CALIB;
    bme_humidity += BME280_HUMIDITY_CALIB;
    bme_pressure += BME280_PRESSURE_CALIB;

    Serial.print("Air temperature: ");
    Serial.print(bme_temperature);
    Serial.println(" °C");
    Serial.print("Humidity: ");
    Serial.print(bme_humidity);
    Serial.println(" %");
    Serial.print("Pressure: ");
    Serial.print(bme_pressure);
    Serial.println(" Pa");
    Serial.print("Water temperature: ");
    Serial.print(ds_temperature);
    Serial.println(" °C");
}



/* Put ESP32 in deep sleep mode */
void deepsleep() 
{
    WiFi.mode(WIFI_OFF);

    Serial.print("Going to sleep, waking up in ");
    Serial.print(DEEPSLEEP_WAKEUP_TIMER/60000000);
    Serial.println(" minutes");

    esp_sleep_enable_timer_wakeup(DEEPSLEEP_WAKEUP_TIMER);
    esp_deep_sleep_start();
}

void setup()
{
    boot_time = millis();
    Serial.begin(115200);

    //Wait while serial starts up
    while(!Serial); 

    //Increment boot count and print it to serial
    ++bootCount; 
    Serial.println("Boot number: " + String(bootCount));

    //Setting up esp_now
    espnow_setup();

    //Setting up all sensors
    Serial.println("Setting up sensors");
    //DS18B20
    ds.begin(); 
    //BME280
    bme280_connect(); 

    pinMode(windSpeedPin, INPUT_PULLUP);
}

void loop() 
{
    wind_Speed(windSpeedPin, 4);
    windDirection(windDirectionPin);
    get_avg_values();

    String output;
    DynamicJsonDocument doc(1024);

    float AirTemp = roundf(bme_temperature * 10) / 10;
    float Humidity = roundf(bme_humidity * 10) / 10;
    float Pressure = roundf(bme_pressure * 10) / 10;
    float WaterTemp = roundf(ds_temperature * 10) / 10;
    float WindSpeed = roundf(wind_speed * 10) / 10;

    doc["AirTemp"] = AirTemp;
    doc["Humidity"] = Humidity;
    doc["Pressure"] = Pressure;
    doc["WaterTemp"] = WaterTemp;
    doc["WindSpeed"] = WindSpeed;
    doc["WindDir"] = DirectionDeg;

    serializeJson(doc, output);

    //sending the data to reciever
    esp_err_t result = esp_now_send(broadcastAddress, (uint8_t *) output.c_str(), output.length() + 1);


    Serial.print("Time since wakeup: ");
    Serial.print(millis()-boot_time);
    Serial.println(" ms");

    deepsleep();
}