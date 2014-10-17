//This is an example of how you would control 1 stepper

#include <AccelStepper.h>

int motorSpeed = 2000; //maximum steps per second (about 3rps / at 16 microsteps)
int motorAccel = 10000; //steps/second/second to accelerate

//int motorDirPin = 2; //digital pin 2
//int motorStepPin = 3; //digital pin 3

int pin1 = 3;
int pin2 = 12;
int pin3 = 11;
int pin4 = 13;

//set up the accelStepper intance
//the "1" tells it we are using a driver
AccelStepper stepper(4, pin1, pin2, pin3, pin4); 

void setup(){
  stepper.setMaxSpeed(motorSpeed);
  stepper.setSpeed(motorSpeed);
  stepper.setAcceleration(motorAccel);
  
  stepper.moveTo(200); //move 32000 steps (should be 10 rev)
}

void loop(){
  
  //if stepper is at desired location
  if (stepper.distanceToGo() == 0){
    delay(500);
    //go the other way the same amount of steps
    //so if current position is 400 steps out, go position -400
    stepper.moveTo(-stepper.currentPosition()); 
  }
  

  
  //these must be called as often as possible to ensure smooth operation
  //any delay will cause jerky motion
  stepper.run();
}
