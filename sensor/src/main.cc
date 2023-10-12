
#include "data.hh"
#include <Arduino.h>

void setup()
{

    uint8_t buf[256];
    sensor_data data;
    data::encode(data, buf, sizeof(buf));
}

void loop() {}