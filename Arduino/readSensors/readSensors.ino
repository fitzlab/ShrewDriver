/*
  Sensor Arduino
	
	Listens for inputs from lick sensor, infrared sensor, and tap sensor.
	Forwards those to PC.

*/

#include <CapacitiveSensor.h>


#define PIN_IR_SENSOR A0
#define PIN_TAP_SENSOR A1
#define PIN_LICK_SENSOR 2
#define PIN_IR_LED 4
#define PIN_CAPACITIVE_GROUND 8

#define TAP_ON HIGH
#define TAP_OFF LOW

#define IR_BROKEN HIGH
#define IR_SOLID LOW

#define LICK_OFF HIGH
#define LICK_ON LOW

int irThresholdLow = 75;
int irThresholdHigh = 100;
bool irPrev = IR_SOLID;

int tapThreshold = 2;
bool tapState = TAP_OFF;

int lickThreshold = 2000; //2000+ = licking, less = not licking.
bool prevLick = LICK_OFF;

const int irBufferSize = 10;
int irBuffer[irBufferSize];
int irBufferPos = 0;

CapacitiveSensor csLick = CapacitiveSensor(PIN_CAPACITIVE_GROUND,PIN_LICK_SENSOR);

void setup() {
  delay(200); //let arduino wake up properly
  Serial.begin(57600);

	//pin setup
  pinMode(PIN_IR_SENSOR, INPUT);
	pinMode(PIN_TAP_SENSOR, INPUT);
  pinMode(PIN_LICK_SENSOR, INPUT_PULLUP);
  pinMode(PIN_IR_LED, OUTPUT);
}

void checkTap(){
	int tap = analogRead(PIN_TAP_SENSOR);
	if(tapState == TAP_OFF && tap > tapThreshold){
		tapState = TAP_ON;
    //Serial.println("Tx");
	}
	else if(tapState == TAP_ON && tap <= tapThreshold){
		tapState = TAP_OFF;
    //Serial.println("To");
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
	checkIR();
	checkLick();
	//checkTap();
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
	long lickReading =  csLick.capacitiveSensor(50);
	if(prevLick == LICK_OFF && lickReading >= lickThreshold){
		//there was a lick, alert the media
    Serial.println("Lx");
    prevLick = LICK_ON;
	}
  else if(prevLick == LICK_ON && lickReading <= lickThreshold){
    Serial.println("Lo");
    prevLick = LICK_OFF;
  }
}









