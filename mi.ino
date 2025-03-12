#include <AFMotor.h>
#include <Servo.h>

AF_DCMotor motor1(1);  // Left Top
AF_DCMotor motor2(2);  // Left Bottom
AF_DCMotor motor3(3);  // Right Bottom
AF_DCMotor motor4(4);  // Right Top

Servo myservo;
String inputString = "";

void setup() {
  Serial.begin(9600);
  setSpeed(180);
  myservo.attach(10);  // Servo on pin 10
  Serial.println("Arduino Ready");
}

void loop() {
  // Commands handled asynchronously via serialEvent
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      handleCommand(inputString);
      inputString = "";
    } else {
      inputString += inChar;
    }
  }
}

void handleCommand(String cmd) {
  cmd.trim();
  int sepIndex = cmd.indexOf(':');
  String action = (sepIndex != -1) ? cmd.substring(0, sepIndex) : cmd;
  int value = (sepIndex != -1) ? cmd.substring(sepIndex + 1).toInt() : -1;

  if (action == "F") {
    if (value >= 0) setSpeed(value);
    moveAll(FORWARD);
    Serial.println("Moving Forward at speed " + String(value));
  } 
  else if (action == "B") {
    if (value >= 0) setSpeed(value);
    moveAll(BACKWARD);
    Serial.println("Moving Backward at speed " + String(value));
  } 
  else if (action == "L") {
    if (value >= 0) setSpeed(value);
    motor1.run(BACKWARD);
    motor2.run(BACKWARD);
    motor3.run(FORWARD);
    motor4.run(FORWARD);
    Serial.println("Turning Left at speed " + String(value));
  } 
  else if (action == "R") {
    if (value >= 0) setSpeed(value);
    motor1.run(FORWARD);
    motor2.run(FORWARD);
    motor3.run(BACKWARD);
    motor4.run(BACKWARD);
    Serial.println("Turning Right at speed " + String(value));
  } 
  else if (action == "S") {
    stopMotors();
    Serial.println("Stopped");
  } 
  else if (action == "SERVO") {
    if (value >= 0 && value <= 180) {
      myservo.write(value);
      Serial.println("Servo set to " + String(value) + "°");
    } else {
      Serial.println("Invalid Servo Angle");
    }
  } 
  else if (action == "SWEEP") {
    sweepServo();
    Serial.println("Servo Sweeping");
  } 
  else {
    Serial.println("Unknown Command: " + cmd);
  }
}

void setSpeed(int spd) {
  spd = constrain(spd, 0, 255);
  motor1.setSpeed(spd);
  motor2.setSpeed(spd);
  motor3.setSpeed(spd);
  motor4.setSpeed(spd);
}

void moveAll(uint8_t direction) {
  motor1.run(direction);
  motor2.run(direction);
  motor3.run(direction);
  motor4.run(direction);
}

void stopMotors() {
  motor1.run(RELEASE);
  motor2.run(RELEASE);
  motor3.run(RELEASE);
  motor4.run(RELEASE);
}

void sweepServo() {
  for (int pos = 0; pos <= 180; pos++) {
    myservo.write(pos);
    delay(10);
  }
  for (int pos = 180; pos >= 0; pos--) {
    myservo.write(pos);
    delay(10);
  }
}
