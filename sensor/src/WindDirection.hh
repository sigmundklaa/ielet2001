#include <Arduino.h>

#define MEASUREMENT_AMOUNT 10 //how many times to measure 
#define MEASUREMENT_MIN_COUNT 5 //minimum amount to count as that direction
#define MEASUREMENT_INTERVAL 500

//Define direction based on measured values for each direction
const int lowerN = 3039;
const int upperN = 3125;
const int lowerNNE = 1450; //1420
const int upperNNE = 1600;
const int lowerNE = 1704;
const int upperNE = 1750;
const int lowerENE = 150; //190
const int upperENE = 210;
const int lowerE = 219;
const int upperE = 245;
const int lowerESE = 80; //115
const int upperESE = 140;
const int lowerSE = 595;
const int upperSE = 619;
const int lowerSSE = 300; //370
const int upperSSE = 500;
const int lowerS = 991;
const int upperS = 1061;
const int lowerSSW = 750; //850
const int upperSSW = 950;
const int lowerSW = 2386;
const int upperSW = 2439;
const int lowerWSW = 2250; //2320
const int upperWSW = 2370;
const int lowerW = 3883;
const int upperW = 3990;
const int lowerWNW = 3150; //3280
const int upperWNW = 3400;
const int lowerNW = 3447;
const int upperNW = 3661;
const int lowerNNW = 2600; //2740
const int upperNNW = 2850;

const String North = "N";
const int NorthDeg = 0;
const String NorthNorthEast = "NNE";
const float NorthNorthEastDeg = 337.5;
const String NorthEast = "NE";
const int NorthEastDeg = 315;
const String EastNorthEast = "ENE";
const float EastNorthEastDeg = 292.5;
const String East = "E";
const int EastDeg = 270;
const String EastSouthEast = "ESE";
const float EastSouthEastDeg = 247.5;
const String SouthEast = "SE";
const int SouthEastDeg = 225;
const String SouthSouthEast = "SSE";
const float SouthSouthEastDeg = 202.5;
const String South = "S";
const int SouthDeg = 180;
const String SouthSouthWest = "SSW";
const float SouthSouthWestDeg = 157.5;
const String SouthWest = "SW";
const int SouthWestDeg = 135;
const String WestSouthWest = "WSW";
const float WestSouthWestDeg = 112.5;
const String West = "W";
const int WestDeg = 90;
const String WestNorthWest = "WNW";
const float WestNorthWestDeg = 67.5;
const String NorthWest = "NW";
const int NorthWestDeg = 45;
const String NorthNorthWest = "NNW";
const float NorthNorthWestDeg = 22.5;
const String Error = "Error";

String Direction = "none";
int DirectionDeg = 0;

int windValue;

void windDirection(int pin) {
  int numMeasurementNorthCount = 0;
  int numMeasurementNorthNorthEastCount = 0;
  int numMeasurementNorthEastCount = 0;
  int numMeasurementEastNorthEastCount = 0;
  int numMeasurementEastCount = 0;
  int numMeasurementEastSouthEastCount = 0;
  int numMeasurementSouthEastCount = 0;
  int numMeasurementSouthSouthEastCount = 0;
  int numMeasurementSouthCount = 0;
  int numMeasurementSouthSouthWestCount = 0;
  int numMeasurementSouthWestCount = 0;
  int numMeasurementWestSouthWestCount = 0;
  int numMeasurementWestCount = 0;
  int numMeasurementWestNorthWestCount = 0;
  int numMeasurementNorthWestCount = 0;
  int numMeasurementNorthNorthWestCount = 0;
  int windValueReading[MEASUREMENT_AMOUNT];
  
  for (int i = 0; i < MEASUREMENT_AMOUNT; i++) {
    // Read the sensor value and store it in an array.
    windValueReading[i] = analogRead(pin);
    delay(MEASUREMENT_INTERVAL);
  }

  for (int i=0; i < MEASUREMENT_AMOUNT; i++) {
    if (windValueReading[i] >= lowerN && windValueReading[i] <= upperN) {
      numMeasurementNorthCount++;
    }
    else if (windValueReading[i] >= lowerNNE && windValueReading[i] <= upperNNE) {
      numMeasurementNorthNorthEastCount++;
    }
    else if (windValueReading[i] >= lowerNE && windValueReading[i] <= upperNE) {
      numMeasurementNorthEastCount++;
    }
    else if (windValueReading[i] >= lowerENE && windValueReading[i] <= upperENE) {
      numMeasurementEastNorthEastCount++;
    }
    else if (windValueReading[i] >= lowerE && windValueReading[i] <= upperE) {
      numMeasurementEastCount++;
    }
    else if (windValueReading[i] >= lowerESE && windValueReading[i] <= upperESE) {
      numMeasurementEastSouthEastCount++;
    }
    else if (windValueReading[i] >= lowerSE && windValueReading[i] <= upperSE) {
      numMeasurementSouthEastCount++;
    }
    else if (windValueReading[i] >= lowerSSE && windValueReading[i] <= upperSSE) {
      numMeasurementSouthSouthEastCount++;
    }
    else if (windValueReading[i] >= lowerS && windValueReading[i] <= upperS) {
      numMeasurementSouthCount++;
    }
    else if (windValueReading[i] >= lowerSSW && windValueReading[i] <= upperSSW) {
      numMeasurementSouthSouthWestCount++;
    }
    else if (windValueReading[i] >= lowerSW && windValueReading[i] <= upperSW) {
      numMeasurementSouthWestCount++;
    }
    else if (windValueReading[i] >= lowerWSW && windValueReading[i] <= upperWSW) {
      numMeasurementWestSouthWestCount++;
    }
    else if (windValueReading[i] >= lowerW && windValueReading[i] <= upperW) {
      numMeasurementWestCount++;
    }
    else if (windValueReading[i] >= lowerWNW && windValueReading[i] <= upperWNW) {
      numMeasurementWestNorthWestCount++;
    }
    else if (windValueReading[i] >= lowerNW && windValueReading[i] <= upperNW) {
      numMeasurementNorthWestCount++;
    }
    else if (windValueReading[i] >= lowerNNW && windValueReading[i] <= upperNNW) {
      numMeasurementNorthNorthWestCount++;
    }
  }

  if (numMeasurementNorthCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(North);
    Direction = North;
    DirectionDeg = NorthDeg;
  }
  else if (numMeasurementNorthNorthEastCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(NorthNorthEast);
    Direction = NorthNorthEast;
    DirectionDeg = NorthNorthEastDeg;
  }
  else if (numMeasurementNorthEastCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(NorthEast);
    Direction = NorthEast;
    DirectionDeg = NorthEastDeg;
  }
  else if (numMeasurementEastNorthEastCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(EastNorthEast);
    Direction = EastNorthEast;
    DirectionDeg = EastNorthEastDeg;
  }
  else if (numMeasurementEastCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(East);
    Direction = East;
    DirectionDeg = EastDeg;
  }
  else if (numMeasurementEastSouthEastCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(EastSouthEast);
    Direction = EastSouthEast;
    DirectionDeg = EastSouthEastDeg;
  }
  else if (numMeasurementSouthEastCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(SouthEast);
    Direction = SouthEast;
    DirectionDeg = SouthEastDeg;
  }
  else if (numMeasurementSouthSouthEastCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(SouthSouthEast);
    Direction = SouthSouthEast;
    DirectionDeg = SouthSouthEastDeg;
  }
  else if (numMeasurementSouthCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(South);
    Direction = South;
    DirectionDeg = SouthDeg;
  }
  else if (numMeasurementSouthSouthWestCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(SouthSouthWest);
    Direction = SouthSouthWest;
    DirectionDeg = SouthSouthWestDeg;
  }
  else if (numMeasurementSouthWestCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(SouthWest);
    Direction = SouthWest;
    DirectionDeg = SouthWestDeg;
  }
  else if (numMeasurementWestSouthWestCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(WestSouthWest);
    Direction = WestSouthWest;
    DirectionDeg = WestSouthWestDeg;
  }
  else if (numMeasurementWestCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(West);
    Direction = West;
    DirectionDeg = WestDeg;
  }
  else if (numMeasurementWestNorthWestCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(WestNorthWest);
    Direction = WestNorthWest;
    DirectionDeg = WestNorthWestDeg;
  }
  else if (numMeasurementNorthWestCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(NorthWest);
    Direction = NorthWest;
    DirectionDeg = NorthWestDeg;
  }
  else if (numMeasurementNorthNorthWestCount >= MEASUREMENT_MIN_COUNT) {
    Serial.println(NorthNorthWest);
    Direction = NorthNorthWest;
    DirectionDeg = NorthNorthWestDeg;
  }
  else {
    Serial.println(Error);
    Direction = Error;
  }

}