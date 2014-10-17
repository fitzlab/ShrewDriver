/*
  Stim-attached Arduino
	
	Does two things: 

	(1)
	Listens for commands to display new gratings (via SPI)
	Forwards those commands via Serial to the stim tablet

	(2)
	Listens for postframe triggers from stim tablet
	Sends those triggers out via digital output pins.
	
	[Theo Walker 2014]

	Thanks to Nick Gammon for his SPI sample code:
	http://gammon.com.au/spi
*/

#include <SPI.h>

#define PIN_GRATING 2
#define PIN_GRAY_SCREEN 3
#define PIN_BLACK_SCREEN 4

char buf [100];
volatile byte pos;
volatile boolean spiCommandReady;

//serial
String serialStr = "";
boolean serialStrReady = false;

void setup (void)
{
  Serial.begin(57600);   // debugging

  pinMode(MISO, OUTPUT); // have to send on master in, *slave out*
  SPCR |= _BV(SPE); // turn on SPI in slave mode
  
  // get ready for an interrupt 
  pos = 0;   // buffer empty
  spiCommandReady = false;

  // now turn on interrupts
  SPI.attachInterrupt();

}


void loop(void){
  if (spiCommandReady){
		//we got a command in, send it to the stim tablet
    buf [pos] = 0;  
    Serial.println (buf);
    pos = 0;
    spiCommandReady = false;
  } 
  
	checkSerial();
} 


void checkSerial(){
	if(Serial.available()){
		char inChar = (char)Serial.read(); 
		if (inChar == '\n'){
			serialStrReady = true;
		} 
		else{
			serialStr += inChar;
		}
	}
	
	if(serialStrReady){
		serialStrReady = false;
		if(serialStr[0] == 'G'){
			//grating
			digitalWrite(PIN_GRATING, HIGH);
			digitalWrite(PIN_GRAY_SCREEN, LOW);
			digitalWrite(PIN_BLACK_SCREEN, LOW);
		}
		else if(serialStr[0] == 'g'){
			//gray
			digitalWrite(PIN_GRATING, LOW);
			digitalWrite(PIN_GRAY_SCREEN, HIGH);
			digitalWrite(PIN_BLACK_SCREEN, LOW);
			
		}
		else if(serialStr[0] == 'b'){
			//black
			digitalWrite(PIN_GRATING, LOW);
			digitalWrite(PIN_GRAY_SCREEN, LOW);
			digitalWrite(PIN_BLACK_SCREEN, HIGH);
		}

    serialStr = "";
	}
}


// SPI interrupt routine
ISR(SPI_STC_vect){
byte c = SPDR;  // grab byte from SPI Data Register
  //add to buffer if room
  if (pos < sizeof buf){
    buf [pos++] = c;
    
    //newline means time to process buffer
    if (c == '\n')
      spiCommandReady = true;
    } 
} 
