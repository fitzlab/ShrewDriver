// Controls a stepper motor via an LCD keypad shield.

#include <LCD4Bit_mod.h> 
#include <AccelStepper.h>

/* -- Constants -- */
#define THREADED_ROD_PITCH 1.25
#define STEPS_PER_REVOLUTION 200
#define MICROSTEPS_PER_STEP 20

int ustepsPerMillimeter = MICROSTEPS_PER_STEP * STEPS_PER_REVOLUTION / THREADED_ROD_PITCH;

/* -- Pin definitions -- */
int motorDirPin = 2;
int motorStepPin = 3;
int triggerPin = 12;


//Key states
int  adc_key_val[5] ={30, 150, 360, 535, 760 };
enum{ KEY_RIGHT, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_SELECT, KEY_NONE};
int NUM_KEYS = 5;
int adc_key_in;
int key=-1;
int oldkey=-1;

/* -- Default Parameters -- */
int motorSpeed = 4000; //maximum steps per second
int motorAccel = 80000; //steps/second/second to accelerate

double mmBolus = 0.1;
double mmUsed = 0.0;

int stepperPos = 0; //in microsteps
char charBuf[16];

/* -- Derived Parameters -- */
int ustepsBolus = 3200; //mmBolus * stepsPerMillimeter;

//for debounce delay
int lastTick = 0;
int debounceTime = 50;

/* -- Initialize libraries -- */
AccelStepper stepper(1, motorStepPin, motorDirPin); //the "1" tells it we are using a driver
LCD4Bit_mod lcd = LCD4Bit_mod(2); 


void setup(){
  /* LCD setup */  
  lcd.init();
  lcd.clear();
  lcd.printIn("SyringePump v0.1");
  lastTick = millis();

  /* Stepper setup */
  stepper.setMaxSpeed(motorSpeed);
  stepper.setSpeed(motorSpeed);
  stepper.setAcceleration(motorAccel);
  
  /* Triggering setup */
  pinMode(triggerPin, INPUT);
}

void loop(){
  //update stepper position
  stepper.run();

  //check for LCD updates
  //readKey();
}

/*
void readKey(){
	//don't poll too often
	long currentTime = millis();
	if ((currentTime-lastTick) < debounceTime){
		return;
	}
	lastTick = currentTime;

	adc_key_in = analogRead(0); // read the value from the sensor  
	key = get_key(adc_key_in); // convert into key press

	if (key != oldkey){
	if (oldkey == KEY_NONE || key == KEY_NONE){
			adc_key_in = analogRead(0);    // read the value from the sensor  
			key = get_key(adc_key_in);            // convert into key press
			if (key != oldkey)        
			{     
				oldkey = key;
				doKeyAction(key);
			}
		}
		else{
			//wait for there to be a KEY_NONE before accepting a new key.
			oldkey = key;
		}
	}  
}

void doKeyAction(unsigned int key){
	if(key == KEY_NONE){
          return;
        }

	String s;

	if(key == KEY_LEFT){
		s = (String("Pulling ") + String(ustepsBolus));
                stepperPos -= ustepsBolus;
		stepper.moveTo(stepperPos);
	}
	if(key == KEY_RIGHT){
		s = (String("Pushing ") + String(ustepsBolus));
                stepperPos += ustepsBolus;
		stepper.moveTo(stepperPos);
	}
	if(key == KEY_UP){
		ustepsBolus += 320;
		s = (String("Bolus ") + String(ustepsBolus));
	}
	if(key == KEY_DOWN){
		ustepsBolus -= 320;
		s = (String("Bolus ") + String(ustepsBolus));
	}
	if(key == KEY_SELECT){
		s = (String("Menu"));
	}
	
	if(key != KEY_NONE){
		//update screen
		lcd.clear();
		s.toCharArray(charBuf, 16);
	        lcd.cursorTo(2, 0);  //line=2, x=0
		lcd.printIn(charBuf);
	}
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
}*/
