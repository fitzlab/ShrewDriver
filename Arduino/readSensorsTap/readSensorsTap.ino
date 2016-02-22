/*
  Sensor Arduino
	
	Listens for inputs from lick sensor and tap sensor.
	Forwards those to PC.

*/

#include <CapacitiveSensor.h>

#define PIN_LICK_SENSOR 4
#define PIN_CAPACITIVE_GROUND_LICK 6

#define PIN_TAP_SENSOR 8
#define PIN_CAPACITIVE_GROUND_TAP 10

#define TAP_ON HIGH
#define TAP_OFF LOW

#define LICK_OFF HIGH
#define LICK_ON LOW

int tapThreshold = 1000;
bool tapState = TAP_OFF;
int numTapSamples = 50;

int lickThreshold = 1000;
bool lickState = LICK_OFF;
int numLickSamples = 50;

CapacitiveSensor csLick = CapacitiveSensor(PIN_CAPACITIVE_GROUND_LICK,PIN_LICK_SENSOR);
CapacitiveSensor csTap = CapacitiveSensor(PIN_CAPACITIVE_GROUND_TAP,PIN_TAP_SENSOR);

void setup() {
  delay(200); //let arduino wake up properly
  Serial.begin(57600);
  Serial.println("Ix");

	//pin setup
	pinMode(PIN_TAP_SENSOR, INPUT);
  pinMode(PIN_LICK_SENSOR, INPUT);
}


void checkLick(){
	long lickReading =  csLick.capacitiveSensor(numLickSamples);
	if(lickState == LICK_OFF && lickReading > lickThreshold){
    lickState = LICK_ON;
    Serial.println("Lx");
	}
  else if(lickState == LICK_ON && lickReading < lickThreshold){
    lickState = LICK_OFF;
    Serial.println("Lo");
  }
}

void checkTap(){
	long tapReading =  csTap.capacitiveSensor(numTapSamples);
	if(tapState == TAP_OFF && tapReading > tapThreshold){
		tapState = TAP_ON;
    Serial.println("Tx");
	}
	else if(tapState == TAP_ON && tapReading < tapThreshold){
		tapState = TAP_OFF;
    Serial.println("To");
	}
}

// the loop routine runs over and over again forever:
void loop() {
	//Check sensors
	checkLick();
	checkTap();
}








