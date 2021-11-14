#include <Arduino.h>
#include <MeMegaPi.h>
#include <Wire.h>
#include <SoftwareSerial.h>

#define SERIAL_COM true
#define BLUETOOTH_COM true

#define BATT_MEASURE_PIN A6
#define BATT_R1 989600
#define BATT_R2 98970
//Encoder Motor
MeEncoderOnBoard Right_Motor(SLOT1);
MeEncoderOnBoard Left_Motor(SLOT2);
MeEncoderOnBoard Arm_Motor(SLOT3);

MeMegaPiDCMotor Gripper_Motor(12);


void isr_process_right_motor(void)
{
      if(digitalRead(Right_Motor.getPortB()) == 0){
            Right_Motor.pulsePosMinus();
      }else{
            Right_Motor.pulsePosPlus();
      }
}

void isr_process_left_motor(void)
{
      if(digitalRead(Left_Motor.getPortB()) == 0){
            Left_Motor.pulsePosMinus();
      }else{
            Left_Motor.pulsePosPlus();
      }
}

void isr_process_arm_motor(void)
{
      if(digitalRead(Arm_Motor.getPortB()) == 0){
            Arm_Motor.pulsePosMinus();
      }else{
            Arm_Motor.pulsePosPlus();
      }
}

#ifdef BLUETOOTH_COM
MeBluetooth bluetooth(PORT_5);
#endif

//input data buffer used by serial and bluetooth coms
#define BUFFSIZE 16
unsigned char databuff[BUFFSIZE] = {0};

void setup() {
  //Set Pwm 8KHz
  TCCR1A = _BV(WGM10);
  TCCR1B = _BV(CS11) | _BV(WGM12);
  TCCR2A = _BV(WGM21) | _BV(WGM20);
  TCCR2B = _BV(CS21);
  
#ifdef SERIAL_COM
  Serial.begin(115200);
#endif
#ifdef BLUETOOTH_COM
  Serial3.begin(115200);
#endif

  //setup drivetrain encoder interrupts
  attachInterrupt(Right_Motor.getIntNum(), isr_process_right_motor, RISING);
  attachInterrupt(Left_Motor.getIntNum(), isr_process_left_motor, RISING);
  attachInterrupt(Arm_Motor.getIntNum(), isr_process_arm_motor, RISING);
  
  Right_Motor.setPosPid(1.8,0,0);
  Left_Motor.setPosPid(1.8,0,0);

  //Arm_Motor.setPulse(7);
  Arm_Motor.setRatio(26.9);
  Arm_Motor.setPosPid(1.8,0,1.2);

  init_arm_pos();

  pinMode(BATT_MEASURE_PIN, INPUT);
  
#ifdef SERIAL_COM
  Serial.write(0x55);Serial.println("STARTED");
#endif
#ifdef BLUETOOTH_COM
  Serial3.write(0x55);Serial3.println("STARTED");
#endif
}

//statistical variables
uint8_t failed_message_count = 0;

//variables to store vehicles states
int8_t gripper_motor_speed = 0;
int8_t left_motor_speed = 0;
int8_t right_motor_speed = 0;
uint8_t arm_angle = 0;

//payload format 
//command payload: [0x55, 0xFA, driveleft_speed, driveright_speed, arm_pos,gripper_speed]
//request payload: [0x55, 0xFB, request_id]
//int count = 1;
void parse_buffer_data(){
  //for(uint8_t i=0; i<BUFFSIZE; i++){
  //  Serial.print(" 0x");Serial.print(databuff[i],HEX);Serial.print(",");
  //}
  //Serial.println();
  if(databuff[0] == 0x55){
    switch(databuff[1]){
      case 0xFA:  //handle a command payload
        left_motor_speed = databuff[2];
        right_motor_speed = databuff[3];
        arm_angle = databuff[4];
        gripper_motor_speed = databuff[5];
        
        //Serial.print("Message Received: [leftdrive: ");Serial.print(left_motor_speed);Serial.print("][rightdrive: ");Serial.print(right_motor_speed);Serial.print("][gripper: ");Serial.print(gripper_motor_speed);Serial.print("][arm angle: ");Serial.print(arm_angle);Serial.println("]");
        //Serial3.print("Message Received: [leftdrive: ");Serial3.print(left_motor_speed);Serial3.print("][rightdrive: ");Serial3.print(right_motor_speed);Serial3.print("][gripper: ");Serial3.print(gripper_motor_speed);Serial3.print("][arm angle: ");Serial3.print(arm_angle);Serial3.println("]");
        //count++;
        update_motors();
        
        break;
      case 0xFB:  //handle a request payload
      
        switch(databuff[2]){
          case 0x00:  //no use right now
          
            break;

//          case 0x11:  //no use right now
//            int batt_analog = analogRead(BATT_MEASURE_PIN);
//            float analog_volt = (batt_analog*5.0)/1024.0;
//            float adjusted_analog = (analog_volt * float(BATT_R1+BATT_R2))/BATT_R2;
//            byte byte_analog = int((adjusted_analog/12.0)*255.0);
//            //Serial.print(analog_volt);Serial.print("  ");Serial.println(adjusted_analog);
//            
//            #ifdef SERIAL_COM
//              Serial.write(0x55);Serial.write(0xFB);Serial.write(0x11);Serial.write(byte_analog);Serial.println();
//            #endif
//            #ifdef BLUETOOTH_COM
//              Serial3.write(0x55);Serial3.write(0xFB);Serial3.write(0x11);Serial3.write(byte_analog);Serial3.println();
//            #endif
//            break;
//            
//          case 0x21:  //no use right now
//            init_arm_pos();
//#ifdef SERIAL_COM
//            Serial.write(0x55);Serial.write(0xFB);Serial.write(0x21);Serial.println();
//#endif
//#ifdef BLUETOOTH_COM
//            Serial3.write(0x55);Serial3.write(0xFB);Serial3.write(0x21);Serial3.println();
//#endif
//            break;
          default:
            //do nothing
            break;
        }
        break;
      default:  //handle the default case, do nothing
        failed_message_count++;
        break;
    }
  }
}

void send_request(){
  memset(databuff, 0, BUFFSIZE);
  databuff[0] = 0x55;
  //databuff[1] = ;
#ifdef SERIAL_COM
  for(uint16_t i=0; i<BUFFSIZE; i++){
    Serial.write(databuff[i]);
  }
  Serial.println();
#endif
  
#ifdef BLUETOOTH_COM
  for(uint16_t i=0; i<BUFFSIZE; i++){
    Serial3.write(databuff[i]);
  }
  Serial3.println();
#endif
}

void init_arm_pos(){
  uint32_t starttime = millis();
  Arm_Motor.setTarPWM(50);
  while(starttime+4000 > millis()){
    Arm_Motor.loop();
  }
  Arm_Motor.setTarPWM(0);
  Arm_Motor.resetEncoderCount();
}

void update_motors(){
  Left_Motor.setTarPWM(map(left_motor_speed, -100, 100, 255, -255));
  Right_Motor.setTarPWM(map(right_motor_speed, -100, 100, -255, 255));
  Arm_Motor.moveTo(map(arm_angle, 0, 90, 0, -1200),200);
  //Serial.println(map(arm_angle, 0, 90, 0, -1200));
}

void loop() {
  
#ifdef SERIAL_COM
  //get serial data and update robot actuators
  if(Serial.available() > 0){
    uint16_t buff_i = 0;
    memset(databuff, 0, BUFFSIZE);
    delay(2);
    //Serial.print("available bytes: ");Serial.println(Serial.available());
    while(Serial.available()){
      databuff[buff_i] = Serial.read();
      buff_i++;
    }
    parse_buffer_data();
  }
#endif
  
#ifdef BLUETOOTH_COM
  //get bluetooth data and update robot actuators
  if(Serial3.available()){
    uint16_t buff_i = 0;
    memset(databuff, 0, BUFFSIZE);
    delay(2);
    while(Serial3.available()){
      databuff[buff_i] = Serial3.read();
      buff_i++;
    }
    parse_buffer_data();
  }
#endif
  
  //update motor controllers
  Right_Motor.loop();
  Left_Motor.loop();
  Arm_Motor.loop();
  //Serial.println(Arm_Motor.getCurPos());
  Gripper_Motor.run(gripper_motor_speed);
  //delay(20);

}
