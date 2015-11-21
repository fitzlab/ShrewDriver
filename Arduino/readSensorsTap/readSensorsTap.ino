/*
  Sensor Arduino
	
	Listens for inputs from lick sensor, infrared sensor, and tap sensor.
	Forwards those to PC.

*/

#include <CapacitiveSensor.h>

#define PIN_IR_SENSOR A0
#define PIN_IR_LED 4

#define PIN_LICK_SENSOR 2
#define PIN_CAPACITIVE_GROUND_LICK 4

#define PIN_TAP_SENSOR 8
#define PIN_CAPACITIVE_GROUND_TAP 10

#define TAP_ON HIGH
#define TAP_OFF LOW

#define IR_BROKEN HIGH
#define IR_SOLID LOW

#define LICK_OFF HIGH
#define LICK_ON LOW

int irThresholdLow = 75;
int irThresholdHigh = 100;
bool irPrev = IR_SOLID;

int tapThreshold = 1000;
bool tapState = TAP_OFF;
int numTapSamples = 50;

int lickThreshold = 1000;
bool lickState = LICK_OFF;
int numLickSamples = 50;

const int irBufferSize = 10;
int irBuffer[irBufferSize];
int irBufferPos = 0;

CapacitiveSensor csLick = CapacitiveSensor(PIN_CAPACITIVE_GROUND_LICK,PIN_LICK_SENSOR);
CapacitiveSensor csTap = CapacitiveSensor(PIN_CAPACITIVE_GROUND_TAP,PIN_TAP_SENSOR);

void setup() {
  delay(200); //let arduino wake up properly
  Serial.begin(57600);
  Serial.println("Ix");

	//pin setup
  pinMode(PIN_IR_SENSOR, INPUT);
	pinMode(PIN_TAP_SENSOR, INPUT);
  pinMode(PIN_LICK_SENSOR, INPUT_PULLUP);
  pinMode(PIN_IR_LED, OUTPUT);
}

void checkIR(){
  getIRSample(); //takes 2ms
  int irLevel = getIRMean(); //way less than 1ms
    
    //Serial.println(irLevel); 
    //delay(100);
	if(irPrev == IR_SOLID && irLevel < irThresholdLow){
		//Something's in the IR beam
		Serial.println("Ix");
    irPrev = IR_BROKEN;
	}
	else if(irPrev == IR_BROKEN && irLevel > irThresholdHigh){
		Serial.println("Io");
    irPrev = IR_SOLID;
	}
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

void getIRSample(){
    // read background level
  delay(1); //let LED turn off properly from last loop
  int bg0 = analogRead(PIN_IR_SENSOR);
  
  //turn on LED and read signal
  digitalWrite(PIN_IR_LED,HIGH);
  delay(1);
  int signal0 = analogRead(PIN_IR_SENSOR);
  
  //turn LED off again.
  digitalWrite(PIN_IR_LED,LOW);
  
  irBuffer[irBufferPos] = signal0-bg0;
  
  
  irBufferPos++;
  if(irBufferPos == irBufferSize){
     irBufferPos = 0; 
  }
}

int getIRMean(){
  int sum=0;
  for(int i = 0; i < irBufferSize; i++){
    sum+=irBuffer[i];
  }
  return (sum*10)/irBufferSize;
}

// the loop routine runs over and over again forever:
void loop() {
	//Check sensors
	//checkIR();
	checkLick();
	checkTap();
}








