/*
  Nanode code for the Uv/Vino project
  This program waits to be activated and starts to read the analog
  port while blinking the led along it produces comma separated values
  giving the milisecond run time and the raw bit value of the portread.
  
  This code is in the public domain. ( vtechinc@xs4all.nl )
 */
 
// Pin 6 has an LED connected on nanode.
// give it a name:
int led = 6;
// time will be in millis (milliseconds)
unsigned long time;

int running = 0;
int inbyte = 0; 

// the setup routine runs once when you press reset:
void setup() {                
  // initialize the digital pin as an output.
  analogReference(EXTERNAL);  // Set AREF to 3.3V
  pinMode(led, OUTPUT);    
  Serial.begin(9600);
  establishContact(); 
}

// the loop routine runs over and over again forever:
void loop() {
  if (Serial.available() > 0) {
    // get incoming byte:
    inbyte = Serial.read();
    if (inbyte == 48){
      establishContact();      
    }
    //Serial.print("inbyte: ");
    //Serial.println(inbyte);
    
  }
  digitalWrite(led, HIGH);   // turn the LED on (HIGH is the voltage level)
  delay(125);               // wait 
  digitalWrite(led, LOW);    // turn the LED off by making the voltage LOW
  delay(125);               // wait f
  time=millis();
  int sensorValue = analogRead(A0);
  Serial.print(time); 
  Serial.print(",");
  Serial.println(sensorValue);
}

void establishContact() {
  Serial.println("UvVino waiting for connection");
  
  while (Serial.available() <= 0) {
    delay(1000);
  }
}
