#define KEY_SELECT 0
#define KEY_RIGHT 1
#define KEY_LEFT 2
#define KEY_DOWN 3
#define KEY_UP 4
#define KEY_NONE 5

//Upper limits for each key
int keyCutoffs[] = {714, //select
              835, //right
              879, //left
              917, //down
              977, //up
              1024}; //max value of analogRead

#define Nkeys ((int)6)

// include the library code:
#include <LiquidCrystal.h>
 
// initialize the library with the numbers of the interface pins
LiquidCrystal lcd(8, 9, 4, 5, 6, 7);
 
int sensorValue;

void setup() 
{
  // set up the LCD's number of columns and rows: 
  lcd.begin(16, 2);
  // Print a message to the LCD.
  lcd.print("hello, world!");
  sensorValue  = 1023;
  Serial.begin(57600); 
}
 
void loop() 
{
   sensorValue = analogRead(A0);
   lcd.setCursor(0, 1);
   lcd.print(sensorValue);   
    int keyNum = getKeyNum(sensorValue);
    char* keyStr = getKeyName(keyNum);
    lcd.print(": ");
    lcd.print(keyStr);
}


int getKeyNum(int value){
  //given an analogRead value (0-1024), return key associated with that value.
  for(int i=0; i<Nkeys; i++){
     if (value < keyCutoffs[i]){
        return i;
     }
  }
}

char* getKeyName(int keyNum){
  //Returns a string of length 8 telling what key was pressed.
  //Used for display, may be handy for debugging.
  switch(keyNum){
    case KEY_SELECT:
      return "Select  ";
    break;
    case KEY_LEFT:
      return "Left    ";
    break;
    case KEY_RIGHT:
      return "Right   ";
    break;
    case KEY_UP:
      return "Up      ";
    break;
    case KEY_DOWN:
      return "Down    ";
    break;
    case KEY_NONE:
      return "No Key  ";
    break;
  }
}

