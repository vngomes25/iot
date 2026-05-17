#include <Arduino.h>

const int trigPin = 9;
const int echoPin = 10;
const float ALTURA_CAIXA_CM = 100.0;

void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duracao = pulseIn(echoPin, HIGH);
  float distancia = duracao * 0.034 / 2;
  float nivel = ALTURA_CAIXA_CM - distancia;
  float porcentagem = constrain((nivel / ALTURA_CAIXA_CM) * 100, 0, 100);

  Serial.print("NIVEL:");
  Serial.println(porcentagem);

  delay(5000);
}