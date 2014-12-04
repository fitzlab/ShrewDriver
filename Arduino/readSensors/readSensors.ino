/*
  Sensor Arduino
	
	Listens for inputs from lick sensor and infrared sensor
	Forwards those to PC.

*/

#define PIN_IR_SENSOR A0
#define PIN_LICK_SENSOR 2
#define PIN_IR_LED 4

#define IR_BROKEN HIGH
#define IR_SOLID LOW

#define LICK_OFF HIGH
#define LICK_ON LOW

int irBaseline;
int irThresholdLow = 15;
int irThresholdHigh = 35;
bool irPrev = IR_SOLID;

int lickThreshold = 1; //0 = licking, other = not licking.
bool prevLick = LICK_OFF;

const int irBufferSize = 10;
int irBuffer[irBufferSize];
int irBufferPos = 0;

void setup() {
  delay(200); //let arduino wake up properly
  Serial.begin(57600);

	//pin setup
  pinMode(PIN_IR_SENSOR, INPUT);
  pinMode(PIN_LICK_SENSOR, INPUT_PULLUP);
  pinMode(PIN_IR_LED, OUTPUT);
}


void getIRSample(){
    // read background level
  int bg0 = analogRead(PIN_IR_SENSOR);
  
  //turn on LED and read signal
  digitalWrite(PIN_IR_LED,HIGH);
  int signal0 = analogRead(PIN_IR_SENSOR);
  delay(2);
  int signal1 = analogRead(PIN_IR_SENSOR);
  
  //turn off LED and read background level again  
  digitalWrite(PIN_IR_LED,LOW);
  delay(2);
  int bg1 = analogRead(PIN_IR_SENSOR);
  
  //calculate
  irBuffer[irBufferPos] = signal0+signal1-bg0-bg1;
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
}

void checkIR(){
  getIRSample();
  int irLevel = getIRMean();
  
    //Serial.println(irLevel);
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









