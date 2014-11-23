/*
  Sensor Arduino
	
	Listens for inputs from lick sensor and infrared sensor
	Forwards those to PC.

*/

#define PIN_IR_SENSOR A0
#define PIN_LICK_SENSOR 2

#define IR_BROKEN HIGH
#define IR_SOLID LOW

#define LICK_OFF HIGH
#define LICK_ON LOW

int irBaseline;
int irThresholdLow;
int irThresholdHigh;
bool irPrev = IR_SOLID;

int lickThreshold = 1; //0 = licking, other = not licking.
bool prevLick = LICK_OFF;

void setup() {
  delay(200); //let arduino wake up properly
  Serial.begin(57600);

	//pin setup
  pinMode(PIN_IR_SENSOR, INPUT);
  pinMode(PIN_LICK_SENSOR, INPUT_PULLUP);
	
	//init IR
	getBaselineIR();

}

// the loop routine runs over and over again forever:
void loop() {
	//Check sensors
	checkIR();
	checkLick();
}

void checkIR(){
  int irLevel = analogRead(PIN_IR_SENSOR);
	if(irPrev == IR_SOLID && irLevel < irThresholdLow){
		//Something's in the IR beam
		Serial.println("Ix");
    //Serial.println(analogRead(PIN_IR_SENSOR));
    irPrev = IR_BROKEN;
	}
	else if(irPrev == IR_BROKEN && irLevel > irThresholdHigh){
		Serial.println("Io");
		//Serial.println(analogRead(PIN_IR_SENSOR));
    irPrev = IR_SOLID;
	}
}

void checkLick(){
  int lickReading = digitalRead(PIN_LICK_SENSOR);
  if(prevLick == LICK_OFF && lickReading == LOW){
    //there was a lick, alert the media
    Serial.println("Lx");
    prevLick = LICK_ON;
  }
  else if(prevLick == LICK_ON && lickReading == HIGH){
    Serial.println("Lo");
    prevLick = LICK_OFF;
  }
}

void getBaselineIR(){
  //get a baseline -- average of the first 10 samples we see
	double sum = 0.0;
  for(int i = 0; i < 10; i++){
    sum += analogRead(PIN_IR_SENSOR);
    delay(5); // delay in between reads for stability
  }
	irBaseline = sum / 10;
	irThresholdLow = irBaseline * 0.7;  //<---- Retest these thresholds on the actual cage! 
	irThresholdHigh = irBaseline * 0.9; //<---- Have only tried it on a lab bench...
	//Serial.println(irBaseline);
}














