const int startPin = 23;
const int powerIn = 4;
int powerState = 0;
void setup() {
  Serial.begin(115200);
  pinMode(powerIn, INPUT);
  pinMode(startPin, OUTPUT);
  powerState = digitalRead(powerIn);
  Serial.println(powerState);
/*  delay(30000);
  digitalWrite(startPin, HIGH);
  delay(100);
  digitalWrite(startPin, LOW);*/
  if (powerState == LOW) {
    delay(30000);
    digitalWrite(startPin, HIGH);
    delay(100);
    digitalWrite(startPin, LOW);
}
}
void loop() {


}
