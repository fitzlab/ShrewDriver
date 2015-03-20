/*
TrainingSimulator

So, rather than have a whole training rig, wouldn't it be nice if you could just have a button for each
sensor and use them to send fake inputs? Yeah it would! This is that.
*/

// pin numbers
const int tapPin = 2;     // the number of the pushbutton pin
const int lickPin = 3;     // the number of the pushbutton pin
const int irPin = 4;     // the number of the pushbutton pin

// state vars
int tapState = 0;         // variable for reading the pushbutton status
int irState = 0;         // variable for reading the pushbutton status
int lickState = 0;         // variable for reading the pushbutton status

void setup() {
  // pin inits
  pinMode(tapPin, INPUT);  
  digitalWrite(tapPin, HIGH); //enable pullup resistor  
  pinMode(lickPin, INPUT);  
  digitalWrite(lickPin, HIGH); //enable pullup resistor  
  pinMode(irPin, INPUT);  
  digitalWrite(irPin, HIGH); //enable pullup resistor  

  Serial.begin(57600);
}

void loop(){
  // read button states. Remember, button is HIGH when *not* pressed and LOW when pressed.

  if(tapState == HIGH && digitalRead(tapPin) == LOW){
    //high to low, button pressed
     Serial.println("Tx"); 
     tapState = LOW;
  }
  if(tapState == LOW && digitalRead(tapPin) == HIGH){
    //low to high, button released
    Serial.println("To"); 
     tapState = HIGH;
  }

  if(lickState == HIGH && digitalRead(lickPin) == LOW){
    //high to low, button pressed
     Serial.println("Lx"); 
     lickState = LOW;
  }
  if(lickState == LOW && digitalRead(lickPin) == HIGH){
    //low to high, button released
    Serial.println("Lo"); 
    lickState = HIGH;
  }

  if(irState == HIGH && digitalRead(irPin) == LOW){
    //high to low, button pressed
     Serial.println("Ix"); 
     irState = LOW;
  }
  if(irState == LOW && digitalRead(irPin) == HIGH){
    //low to high, button released
    Serial.println("Io"); 
    irState = HIGH;
  }

  delay(40); //debounce
}
