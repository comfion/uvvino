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
// define inject switch connected to digital port 7
int injector_switch = 7;

int valve_a = 10;  // valve a connected to pin 10
int valve_b = 12; // b to 12
int valve_c = 13; // c t

int running = 0;
int inbyte = 0; 

// the setup routine runs once when you press reset:
void setup() {                
  // initialize the digital pin as an output.
  analogReference(EXTERNAL);  // Set AREF to 3.3V
  pinMode(led, OUTPUT);
  pinMode(valve_a, OUTPUT);
  pinMode(valve_b, OUTPUT);  
  pinMode(13, OUTPUT);    
  Serial.begin(9600);
  pinMode(injector_switch, INPUT);
}

// the loop routine runs over and over again forever:
void loop() {
  
  if ( digitalRead(injector_switch) > 0) {
    
    //Serial.print("inbyte: ");
    //Serial.println(inbyte);
    
    digitalWrite(led, HIGH);   // turn the LED on (HIGH is the voltage level)
    delay(50);               // wait 
    digitalWrite(led, LOW);    // turn the LED off by making the voltage LOW
    delay(50);               // wait f
    time=millis();
    int sensorValue = analogRead(A0);
    Serial.print(time); 
    Serial.print(",");
    Serial.println(sensorValue);
  }
  
  delay(125);
  
  if (Serial.available() > 0) {
    
    //Serial.println("serial available");
    // Read 3 comma separated integers and open corresponding valve if value > 0
    int valve_a_open = Serial.parseInt(); 
    // do it again:
    int valve_b_open = Serial.parseInt(); 
    // do it again:
    int valve_c_open = Serial.parseInt();     
    
    if (Serial.read() == '\n') {
      
      if (valve_a_open) {
        digitalWrite(valve_a, HIGH);
      }

      if (valve_b_open) {
        digitalWrite(valve_b, HIGH);
      }       
      if (valve_c_open) {
        digitalWrite(valve_c, HIGH);
      }
// close the other valves, after the other valves have been opened to avoid dead valvespace
      
      if (!valve_a_open) {
        digitalWrite(valve_a, LOW);
      }

      if (!valve_b_open) {
        digitalWrite(valve_b, LOW);
      }
      if (!valve_c_open) {
        digitalWrite(valve_c, LOW);
      }

    }
  }
/*
  digitalWrite(valve_c, HIGH);
  delay(2000);
  digitalWrite(valve_c, LOW);
  delay(2000);

  digitalWrite(valve_b, HIGH);
  delay(2000);
  digitalWrite(valve_b, LOW);
  delay(2000);

  digitalWrite(valve_a, HIGH);
  delay(2000);
  digitalWrite(valve_a, LOW);

  delay(5000);

  digitalWrite(valve_a, HIGH);
  delay(1000);
  digitalWrite(valve_b, HIGH);
  delay(1000);
  digitalWrite(valve_c, HIGH);
  delay(5000);
  digitalWrite(valve_a, LOW);
  delay(1000);
  digitalWrite(valve_b, LOW);
  delay(1000);
  digitalWrite(valve_c, LOW);
  delay(1000);

*/


}


