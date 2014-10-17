// Control a stepper motor via the Adafruit LCD keypad shield.

//stepper includes
#include <AccelStepper.h>

// Adafruit LCD includes
#include <Wire.h>
#include <Adafruit_MCP23017.h>
#include <Adafruit_RGBLCDShield.h>

/* -- Constants -- */
#define SYRINGE_VOLUME_ML 30.0
#define SYRINGE_BARREL_LENGTH_MM 80.0

#define THREADED_ROD_PITCH 1.25
#define STEPS_PER_REVOLUTION 200.0
#define MICROSTEPS_PER_STEP 1.0 //this is 1.0 if using Arduino motor shield, or 16.0 if using Easy Driver.

long ustepsPerMM = MICROSTEPS_PER_STEP * STEPS_PER_REVOLUTION / THREADED_ROD_PITCH;
long ustepsPerML = (MICROSTEPS_PER_STEP * STEPS_PER_REVOLUTION * SYRINGE_BARREL_LENGTH_MM) / (SYRINGE_VOLUME_ML * THREADED_ROD_PITCH );

int stepsPerMillimeter = STEPS_PER_REVOLUTION / THREADED_ROD_PITCH;

// Bolus menu increments
const int mLBolusStepsLength = 9;
float mLBolusSteps[9] = {0.001, 0.005, 0.010, 0.050, 0.100, 0.500, 1.000, 5.000, 10.000};

//enums
enum{PUSH,PULL}; //plunger movement directions
enum{MAIN, BOLUS_MENU}; //UI states

//debounce
long prevKeyTime = millis();
long debouncePeriod = 120; //min ms between key presses

/* -- Parameters you may want to change -- */
float mLBolus = 0.1; //default bolus size (mL)
int mLBolusStepIdx = 3; //0.05 mL increments at first
float mLBolusStep = mLBolusSteps[mLBolusStepIdx];

//motor properties
int motorSpeed = 200; //maximum steps per second
int motorAccel = 200; //steps/second/second to accelerate

/* -- Variables -- */
float mLUsed = 0.0; //mL used, for display (cannot be negative)
long stepperPos = 0; //current position in microsteps
char charBuf[16];

//menu stuff
int uiState = MAIN;

//triggering
int prevTriggerState = HIGH;

/* -- Pin definitions -- */
const int pwmA = 3;
const int pwmB = 11;
const int brakeA = 8;
const int brakeB = 9;
const int dirA = 12;
const int dirB = 13;
const int triggerPin = A3;

/* -- Initialize stepper and LCD objects -- */
Adafruit_RGBLCDShield lcd = Adafruit_RGBLCDShield();
AccelStepper stepper(2,dirA,dirB);

void setup(){
  /*-- LCD setup --*/
  lcd.begin(16, 2);
  lcd.setBacklight(0x7); //turn on backlight
	lcd.setCursor(0,0);  //column 0 row 1
  lcd.print("SyringePump v0.2");

  /*-- Stepper setup --*/
  pinMode(pwmA, OUTPUT);
  pinMode(pwmB, OUTPUT);
  pinMode(brakeA, OUTPUT);
  pinMode(brakeB, OUTPUT);
  
  digitalWrite(pwmA, HIGH);
  digitalWrite(pwmB, HIGH);
  digitalWrite(brakeA, LOW);
  digitalWrite(brakeB, LOW);
  
  stepper.setMaxSpeed(motorSpeed);
  stepper.setSpeed(motorSpeed);
  stepper.setAcceleration(motorAccel);
  
	/* -- Triggering -- */
  pinMode(triggerPin, INPUT);
	digitalWrite(triggerPin, HIGH); //pull pin high to prevent noise triggering

	/* -- Serial -- */
	Serial.begin(9600);
}

void loop(){
  stepper.run(); //call as often as possible for smooth stepping
	
	Serial.println(analogRead(A0));

	if (stepper.distanceToGo() == 0){
		//check trigger line for low-to-high signals
		checkTrigger();
	}

	if (stepper.distanceToGo() == 0){
		//check keypad for new user input
		readKeypad();
	}
}


void readKeypad(){
	long currentTime = millis();
	if(currentTime - prevKeyTime < debouncePeriod){
		return;
	}
	prevKeyTime = currentTime;

  uint8_t buttons = lcd.readButtons();  


	if (!buttons) {
    return;
	}

	if(buttons & BUTTON_SELECT){
		if(uiState == MAIN){
			uiState = BOLUS_MENU;
		}
		else if(uiState == BOLUS_MENU){
			uiState = MAIN;
		}
	}

	String s1; //upper line
	String s2; //lower line
	
	if(uiState == MAIN){
		if(buttons & BUTTON_LEFT){
			s2 = (String("Pull ") + decToString(mLBolus) + String(" mL"));
			bolus(PULL);
		}
		if(buttons & BUTTON_RIGHT){
			s2 = (String("Push ") + decToString(mLBolus) + String(" mL"));
			bolus(PUSH);
		}
		if(buttons & BUTTON_UP){
			mLBolus += mLBolusStep;
		}
		if(buttons & BUTTON_DOWN){
			if((mLBolus - mLBolusStep) > 0){
			  mLBolus -= mLBolusStep;
			}
			else{
			  mLBolus = 0;
			}
		}
		s1 = String("Used ") + decToString(mLUsed) + String(" mL");
		s2 = (String("Bolus ") + decToString(mLBolus) + String(" mL"));		
	}
	else if(uiState == BOLUS_MENU){
		if(buttons & BUTTON_LEFT){
			//nothin'
		}
		if(buttons & BUTTON_RIGHT){
			//nothin'
		}
		if(buttons & BUTTON_UP){
			if(mLBolusStepIdx < mLBolusStepsLength-1){
				mLBolusStepIdx++;
				mLBolusStep = mLBolusSteps[mLBolusStepIdx];
			}
		}
		if(buttons & BUTTON_DOWN){
			if(mLBolusStepIdx > 0){
				mLBolusStepIdx -= 1;
				mLBolusStep = mLBolusSteps[mLBolusStepIdx];
			}
		}
		s1 = String("Menu> BolusStep");
		s2 = decToString(mLBolusStep);
	}

	//update screen
	lcd.clear();

	s2.toCharArray(charBuf, 16);
	lcd.setCursor(0,0);  //column 0 row 0
	lcd.print(charBuf);
	
	s1.toCharArray(charBuf, 16);
	lcd.setCursor(0,1);  //column 0 row 1
	lcd.print(charBuf);
		
}


void bolus(int direction){
	//Pushes or pulls a bolus of liquid.
	//Change units to steps, update mLUsed, and move motor
	long steps;
	if(direction == PUSH){
		steps = mLBolus * ustepsPerML;
		mLUsed += mLBolus;
	}
	else if(direction == PULL){
		steps = -mLBolus * ustepsPerML;
		if((mLUsed-mLBolus) > 0){
			mLUsed -= mLBolus;
		}
		else{
			mLUsed = 0;
		}
	}	
	stepperPos += steps;
	stepper.moveTo(stepperPos);
}

void checkTrigger(){
		//look for a low-to-high signal on the trigger pin
    int triggerValue = digitalRead(triggerPin);
    if(triggerValue == HIGH && prevTriggerState == LOW){
      bolus(PUSH);
    }
    prevTriggerState = triggerValue;
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