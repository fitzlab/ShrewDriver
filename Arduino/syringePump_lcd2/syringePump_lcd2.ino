// Controls a stepper motor via an LCD keypad shield.
// Accepts triggers and serial commands.

#include <LiquidCrystal.h>
#include <LCDKeypad.h>

/* -- Constants -- */
#define SYRINGE_VOLUME_ML 30.0
#define SYRINGE_BARREL_LENGTH_MM 80.0

#define THREADED_ROD_PITCH 1.25
#define STEPS_PER_REVOLUTION 200.0
#define MICROSTEPS_PER_STEP 16.0

#define SPEED_MICROSECONDS_DELAY 200 //longer delay = lower speed

long ustepsPerMM = MICROSTEPS_PER_STEP * STEPS_PER_REVOLUTION / THREADED_ROD_PITCH;
long ustepsPerML = (MICROSTEPS_PER_STEP * STEPS_PER_REVOLUTION * SYRINGE_BARREL_LENGTH_MM) / (SYRINGE_VOLUME_ML * THREADED_ROD_PITCH );

/* -- Pin definitions -- */
int motorDirPin = 2;
int motorStepPin = 3;

int triggerPin = A3;
int bigTriggerPin = A4;

/* -- Keypad -- */
int sensorValue ;
int KeyTable[31];
 
int  adc_key_val[5] ={30, 150, 360, 535, 760 };

enum{ KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_SELECT, KEY_NONE};
int NUM_KEYS = 5;
int adc_key_in;
int key = KEY_NONE;

/* -- Enums and constants -- */
enum{PUSH,PULL}; //syringe movement direction
enum{MAIN, BOLUS_MENU}; //UI states

const int mLBolusStepsLength = 9;
float mLBolusSteps[9] = {0.001, 0.005, 0.010, 0.050, 0.100, 0.500, 1.000, 5.000, 10.000};

/* -- Default Parameters -- */
float mLBolus = 0.500; //default bolus size
float mLBigBolus = 1.000; //default large bolus size
float mLUsed = 0.0;
int mLBolusStepIdx = 3; //0.05 mL increments at first
float mLBolusStep = mLBolusSteps[mLBolusStepIdx];

long stepperPos = 0; //in microsteps
char charBuf[16];

//key and debounce params
long lastKeyRepeatAt = 0;
long keyRepeatDelay = 400;
long keyDebounce = 125;
int prevKey = KEY_NONE;
int selectHoldCount = 0;

//menu stuff
int uiState = MAIN;

//triggering
int prevBigTrigger = HIGH;
int prevTrigger = HIGH;

//serial
String serialStr = "";
boolean serialStrReady = false;

/* -- Initialize libraries -- */
LiquidCrystal lcd(8, 13, 9, 4, 5, 6, 7);

void setup(){
  /* LCD setup */  
  lcd.begin(16, 2);
  lcd.clear();
  pinMode(10, OUTPUT); //disable backlight

  lcd.print("SyringePump v0.4");

  /* Triggering setup */
  pinMode(triggerPin, INPUT);
  pinMode(bigTriggerPin, INPUT);
  digitalWrite(triggerPin, HIGH); //enable pullup resistor
  digitalWrite(bigTriggerPin, HIGH); //enable pullup resistor
  
  /* Motor Setup */
  pinMode(motorStepPin, OUTPUT);
  pinMode(motorDirPin, OUTPUT);
  
  /* Serial setup */
  //Note that serial commands must be terminated with a newline
  //to be processed. Check this setting in your serial monitor if 
  //serial commands aren't doing anything.
  Serial.begin(57600); //Note that your serial connection must be set to 57600 to work!
}

void loop(){
  //check for LCD updates
  readKey();
  
  //look for triggers on trigger lines
  checkTriggers();
  
  //check serial port for new commands
  readSerial();
	if(serialStrReady){
		processSerial();
	}
}

void checkTriggers(){
		//check low-reward trigger line
    int pushTriggerValue = digitalRead(triggerPin);
    if(pushTriggerValue == HIGH && prevTrigger == LOW){
      bolus(PUSH);
			updateScreen();
    }
    prevTrigger = pushTriggerValue;
    
		//check high-reward trigger line
    int bigTriggerValue = digitalRead(bigTriggerPin);
    if(bigTriggerValue == HIGH && prevBigTrigger == LOW){
			//push big reward amount
			float mLBolusTemp = mLBolus;
			mLBolus = mLBigBolus;
			bolus(PUSH);
			mLBolus = mLBolusTemp;

			updateScreen();
    }
    prevBigTrigger = bigTriggerValue;
}

void readSerial(){
		//pulls in characters from serial port as they arrive
		//builds serialStr and sets ready flag when newline is found
		while (Serial.available()) {
			char inChar = (char)Serial.read(); 
			if (inChar == '\n') {
				serialStrReady = true;
			} 
                        else{
			  serialStr += inChar;
                        }
		}
}

void processSerial(){
	//process serial commands as they are read in
        int uLbolus = serialStr.toInt();
        mLBolus = (float)uLbolus / 1000.0;
        if(mLBolus < 0){
          mLBolus = -mLBolus;
    	  bolus(PULL);
        }
        else{
          bolus(PUSH);
        }
        serialStrReady = false;
	serialStr = "";
        updateScreen();
        
        /*
        else{
           Serial.write("Invalid command: ["); 
           char buf[40];
           serialStr.toCharArray(buf, 40);
           Serial.write(buf); 
           Serial.write("]\n"); 
        }
        serialStrReady = false;
	serialStr = "";
      */
}

void bolus(int direction){
        //Move stepper. Will not return until stepper is done moving.        
  
	//change units to steps
	long steps = (mLBolus * ustepsPerML);
	if(direction == PUSH){
                digitalWrite(motorDirPin, HIGH);
		steps = mLBolus * ustepsPerML;
		mLUsed += mLBolus;
	}
	else if(direction == PULL){
                digitalWrite(motorDirPin, LOW);
		if((mLUsed-mLBolus) > 0){
			mLUsed -= mLBolus;
		}
		else{
			mLUsed = 0;
		}
	}	

      float usDelay = SPEED_MICROSECONDS_DELAY; //can go down to 20 or 30
    
      for(int i=0; i < steps; i++){ 
        digitalWrite(motorStepPin, HIGH); 
        delayMicroseconds(usDelay); 
    
        digitalWrite(motorStepPin, LOW); 
        delayMicroseconds(usDelay); 
      } 

}

void readKey(){
	//Some UI niceness here. 
        //When user holds down a key, it will repeat every so often (keyRepeatDelay).
        //But when user presses and releases a key, 
        //the key becomes responsive again after the shorter debounce period (keyDebounce).

	adc_key_in = analogRead(0);
	key = get_key(adc_key_in); // convert into key press

	long currentTime = millis();
        long timeSinceLastPress = (currentTime-lastKeyRepeatAt);
        
        boolean processThisKey = false;
	if (prevKey == key && timeSinceLastPress > keyRepeatDelay){
          processThisKey = true;
        }
        if(prevKey == KEY_NONE && timeSinceLastPress > keyDebounce){
          processThisKey = true;
        }
        if(key == KEY_NONE){
          processThisKey = false;
        }  
        
        //holding the SELECT key will move the pump to position 0
        if (key == KEY_SELECT && prevKey == KEY_SELECT){
            selectHoldCount++;
            if(selectHoldCount > 15000){
                //reset position to 0 mL used
                double savedBolusSize = mLBolus;
                mLBolus = mLUsed;
                bolus(PULL);
                mLBolus = savedBolusSize;
                updateScreen();
            }
        }
        else{
           selectHoldCount = 0; 
        }
                
        prevKey = key;
        
        if(processThisKey){
          doKeyAction(key);
  	  lastKeyRepeatAt = currentTime;
        }
}

void doKeyAction(unsigned int key){
	if(key == KEY_NONE){
        return;
    }

	if(key == KEY_SELECT){
		if(uiState == MAIN){
			uiState = BOLUS_MENU;
		}
		else if(BOLUS_MENU){
			uiState = MAIN;
		}
	}

	if(uiState == MAIN){
		if(key == KEY_LEFT){
			bolus(PULL);
		}
		if(key == KEY_RIGHT){
			bolus(PUSH);
		}
		if(key == KEY_UP){
			mLBolus += mLBolusStep;
		}
		if(key == KEY_DOWN){
			if((mLBolus - mLBolusStep) > 0){
			  mLBolus -= mLBolusStep;
			}
			else{
			  mLBolus = 0;
			}
		}
	}
	else if(uiState == BOLUS_MENU){
		if(key == KEY_LEFT){
			//nothin'
		}
		if(key == KEY_RIGHT){
			//nothin'
		}
		if(key == KEY_UP){
			if(mLBolusStepIdx < mLBolusStepsLength-1){
				mLBolusStepIdx++;
				mLBolusStep = mLBolusSteps[mLBolusStepIdx];
			}
		}
		if(key == KEY_DOWN){
			if(mLBolusStepIdx > 0){
				mLBolusStepIdx -= 1;
				mLBolusStep = mLBolusSteps[mLBolusStepIdx];
			}
		}
	}

	updateScreen();
}

void updateScreen(){
	//build strings for upper and lower lines of screen
	String s1; //upper line
	String s2; //lower line
	
	if(uiState == MAIN){
		s1 = String("Used ") + decToString(mLUsed) + String(" mL");
		s2 = (String("Bolus ") + decToString(mLBolus) + String(" mL"));		
	}
	else if(uiState == BOLUS_MENU){
		s1 = String("Menu> BolusStep");
		s2 = decToString(mLBolusStep);
	}

	//do actual screen update
	lcd.clear();

	s2.toCharArray(charBuf, 16);
	lcd.setCursor(0, 1);  //line=2, x=0
	lcd.print(charBuf);
	
	s1.toCharArray(charBuf, 16);
	lcd.setCursor(0, 0);  //line=1, x=0
	lcd.print(charBuf);
}


// Convert ADC value to key number
int get_key(unsigned int input){
  int k;
  for (k = 0; k < NUM_KEYS; k++){
    if (input < adc_key_val[k]){
      return k;
    }
  }
  if (k >= NUM_KEYS){
    k = KEY_NONE;     // No valid key pressed
  }
  return k;
}

String decToString(float decNumber){
	//not a general use converter! Just good for the numbers we're working with here.
	int wholePart = decNumber; //truncate
	int decPart = round(abs(decNumber*1000)-abs(wholePart*1000)); //3 decimal places
        String strZeros = String("");
        if(decPart < 10){
          strZeros = String("00");
        }  
        else if(decPart < 100){
          strZeros = String("0");
        }
	return String(wholePart) + String('.') + strZeros + String(decPart);
}


// You can stop reading here, this is just keypad / button stuff
void GenerateKeyTable(int vcc,int* array)
{
  float resistor;
 
//////////////1key//////////////////////  
  resistor = ((float)Rup)/(Rbase + Rup);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rdown)/(Rbase + Rdown);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rleft)/(Rbase + Rleft);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rright)/(Rbase + Rright);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rselect)/(Rbase + Rselect);
  *array++ = resistor*vcc;
 
//////////////2 key/////////////////////////
  resistor = ((float)Rup)*Rdown/(Rup+Rdown);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup)*Rright/(Rup+Rright);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup)*Rleft/(Rup+Rleft);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup)*Rselect/(Rup+Rselect);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rdown)*Rleft/(Rdown+Rleft);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rdown)*Rright/(Rdown+Rright);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rdown)*Rselect/(Rdown+Rselect);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rright)*Rleft/(Rright+Rleft);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rright)*Rselect/(Rright+Rselect);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rleft)*Rselect/(Rleft+Rselect);
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  ///////////////3 key//////////////////////
  resistor = ((float)Rup*Rdown*Rright/(Rup*Rright + Rdown*Rright + Rup*Rdown));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup*Rdown*Rleft/(Rup*Rleft + Rdown*Rleft + Rup*Rdown));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup*Rdown*Rselect/(Rup*Rselect + Rdown*Rselect + Rup*Rdown));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rleft*Rdown*Rright/(Rleft*Rright + Rdown*Rright + Rleft*Rdown));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rleft*Rdown*Rselect/(Rleft*Rselect + Rdown*Rselect + Rleft*Rdown));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rleft*Rup*Rright/(Rleft*Rright + Rup*Rright + Rleft*Rup));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rleft*Rup*Rselect/(Rleft*Rselect + Rup*Rselect + Rleft*Rup));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup*Rright*Rselect/(Rup*Rright + Rright*Rselect + Rup*Rselect));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rdown*Rright*Rselect/(Rdown*Rright + Rright*Rselect + Rdown*Rselect));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
 resistor = ((float)Rleft*Rright*Rselect/(Rleft*Rright + Rright*Rselect + Rleft*Rselect));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  ////////////////4 key///////////////////////////
  resistor = ((float)Rup*Rdown*Rleft*Rright/(Rdown*Rleft*Rright + Rup*Rleft*Rright + Rup*Rdown*Rright + Rup*Rdown*Rleft));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup*Rdown*Rleft*Rselect/(Rdown*Rleft*Rselect + Rup*Rleft*Rselect + Rup*Rdown*Rselect + Rup*Rdown*Rleft));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rup*Rselect*Rleft*Rright/(Rselect*Rleft*Rright + Rup*Rleft*Rright + Rup*Rselect*Rright + Rup*Rselect*Rleft));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rselect*Rdown*Rleft*Rright/(Rdown*Rleft*Rright + Rselect*Rleft*Rright + Rselect*Rdown*Rright + Rselect*Rdown*Rleft));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  resistor = ((float)Rselect*Rdown*Rup*Rright/(Rdown*Rup*Rright + Rselect*Rup*Rright + Rselect*Rdown*Rright + Rselect*Rdown*Rup));
  resistor = resistor/(resistor+Rbase);
  *array++ = resistor*vcc;
 
  /////////////////5 key//////////////////////////
  resistor = ((float)Rup*Rdown*Rleft*Rright*Rselect/(Rdown*Rleft*Rright*Rselect + Rup*Rleft*Rright*Rselect + Rup*Rdown*Rright*Rselect + Rup*Rdown*Rleft*Rselect + Rup*Rdown*Rleft*Rright));
  resistor = resistor/(resistor+Rbase);
  *array = resistor*vcc;
}
