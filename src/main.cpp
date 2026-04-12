// =============================================
//   URBAN SENTINEL — 10 Sensor IoT Monitor
//   For VS Code + PlatformIO + Wokwi
// =============================================

#include <Arduino.h>
#include <esp_system.h>
#include <math.h>
#include "DHT.h"

// ── Flood (HC-SR04) ─────────────────────────
#define FLOOD_TRIG   2
#define FLOOD_ECHO   4

// ── Air Quality + Fire (MQ-2) ───────────────
#define MQ2_AO       34
#define MQ2_DO       35

// ── Temperature & Humidity (DHT22) ──────────
#define DHT_PIN      15
#define DHT_TYPE     DHT22
DHT dht(DHT_PIN, DHT_TYPE);

// ── Traffic (Push Buttons) ──────────────────
#define BTN1         13
#define BTN2         14

// ── Noise (KY-040 Rotary Encoder) ───────────
#define ENC_CLK      25
#define ENC_DT       26
#define ENC_SW       33

// ── Street Light (LDR) ──────────────────────
#define LDR_PIN      32
#define STREET_LED   23

// ── Waste Bin (HC-SR04) ─────────────────────
#define BIN_TRIG     5
#define BIN_ECHO     18

// ── Rain (NTC Analog Temp Sensor) ───────────
#define NTC_PIN      12

// ── Parking (HC-SR04 x2) ────────────────────
#define PARK_TRIG_A  16
#define PARK_ECHO_A  17
#define PARK_TRIG_B  19
#define PARK_ECHO_B  21

// ── Buzzer ──────────────────────────────────
#define BUZZER       27

// ── Thresholds ──────────────────────────────
#define BIN_EMPTY_CM      30
#define BIN_FULL_CM        3
#define CAR_PRESENT_CM    20
#define ILLEGAL_PARK_MS   30000

// ── Timing ──────────────────────────────────
#define REPORT_INTERVAL   10000
unsigned long lastReport = 0;

// ── Traffic counters ────────────────────────
int  lane1Count = 0;
int  lane2Count = 0;
bool btn1Prev   = HIGH;
bool btn2Prev   = HIGH;

// ── Noise ───────────────────────────────────
int noiseLevel = 40;
int lastCLK;

// ── Parking timers ──────────────────────────
unsigned long spotAOccupiedSince = 0;
unsigned long spotBOccupiedSince = 0;
bool spotAWasOccupied = false;
bool spotBWasOccupied = false;

// ── Buzzer state ────────────────────────────
unsigned long buzzerStart = 0;
bool buzzerOn = false;

// Simulated sensor state so readings keep evolving even without manual input.
float simFloodDist    = 48.0f;
int   simSmokePct     = 22;
float simTemperature  = 29.0f;
float simHumidity     = 58.0f;
int   simLightPct     = 65;
float simBinDist      = 22.0f;
int   simRainPct      = 10;
int   simRainTemp     = 28;
float simParkDistA    = 40.0f;
float simParkDistB    = 42.0f;
float simTrafficFlow  = 5.0f;
int   rainEpisodeTicks = 0;
int   smokeSpikeTicks  = 0;
bool  simSpotAOccupied = false;
bool  simSpotBOccupied = false;
unsigned long reportCount = 0;
bool  sensorStateInit = false;

// =============================================
//   HELPER FUNCTIONS
// =============================================

float getDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  long duration = pulseIn(echoPin, HIGH, 30000);
  return duration * 0.034 / 2.0;
}

void handleBuzzer() {
  if (buzzerOn && millis() - buzzerStart >= 1000) {
    digitalWrite(BUZZER, LOW);
    buzzerOn = false;
  }
}

void triggerAlarm() {
  if (!buzzerOn) {
    digitalWrite(BUZZER, HIGH);
    buzzerStart = millis();
    buzzerOn    = true;
  }
}

void printDivider() {
  Serial.println("================================");
}

float clampFloat(float value, float minValue, float maxValue) {
  if (value < minValue) return minValue;
  if (value > maxValue) return maxValue;
  return value;
}

float randomFloat(float minValue, float maxValue) {
  return minValue + (random(0, 10001) / 10000.0f) * (maxValue - minValue);
}

bool chance(float probability) {
  return randomFloat(0.0f, 1.0f) < probability;
}

float easeTowards(float current, float target, float blend, float maxStep,
                  float minValue, float maxValue) {
  float delta = (target - current) * blend;
  delta = clampFloat(delta, -maxStep, maxStep);
  return clampFloat(current + delta, minValue, maxValue);
}

int easeTowardsInt(int current, int target, float blend, int maxStep,
                   int minValue, int maxValue) {
  int delta = static_cast<int>((target - current) * blend);
  delta = constrain(delta, -maxStep, maxStep);
  return constrain(current + delta, minValue, maxValue);
}

float distanceToFillPct(float distanceCm) {
  float ratio = (BIN_EMPTY_CM - distanceCm) / (BIN_EMPTY_CM - BIN_FULL_CM);
  return clampFloat(ratio * 100.0f, 0.0f, 100.0f);
}

float fillPctToDistance(float fillPct) {
  float ratio = clampFloat(fillPct, 0.0f, 100.0f) / 100.0f;
  return BIN_EMPTY_CM - ratio * (BIN_EMPTY_CM - BIN_FULL_CM);
}

void initialiseSensorState() {
  if (sensorStateInit) return;

  float floodDist = getDistance(FLOOD_TRIG, FLOOD_ECHO);
  simFloodDist = (floodDist > 0.0f) ? clampFloat(floodDist, 5.0f, 100.0f) : 48.0f;

  simSmokePct = constrain(map(analogRead(MQ2_AO), 0, 4095, 0, 100), 0, 100);

  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  simTemperature = isnan(temperature) ? 29.0f : clampFloat(temperature, 18.0f, 50.0f);
  simHumidity = isnan(humidity) ? 58.0f : clampFloat(humidity, 25.0f, 100.0f);

  simLightPct = constrain(map(analogRead(LDR_PIN), 0, 4095, 0, 100), 0, 100);

  float binDist = getDistance(BIN_TRIG, BIN_ECHO);
  simBinDist = (binDist > 0.0f) ? clampFloat(binDist, BIN_FULL_CM, BIN_EMPTY_CM) : 22.0f;

  int ntcRaw = analogRead(NTC_PIN);
  simRainTemp = constrain(map(ntcRaw, 0, 4095, 50, -10), -10, 50);
  simRainPct = simRainTemp < 20 ? constrain(map(simRainTemp, 20, -10, 0, 100), 0, 100) : 0;

  float distA = getDistance(PARK_TRIG_A, PARK_ECHO_A);
  float distB = getDistance(PARK_TRIG_B, PARK_ECHO_B);
  simParkDistA = (distA > 0.0f) ? clampFloat(distA, 3.0f, 120.0f) : 40.0f;
  simParkDistB = (distB > 0.0f) ? clampFloat(distB, 3.0f, 120.0f) : 42.0f;
  simSpotAOccupied = simParkDistA < CAR_PRESENT_CM;
  simSpotBOccupied = simParkDistB < CAR_PRESENT_CM;

  sensorStateInit = true;
}

// =============================================
//   SETUP
// =============================================

void setup() {
  Serial.begin(115200);
  randomSeed(static_cast<uint32_t>(esp_random()) ^ micros());

  // Flood
  pinMode(FLOOD_TRIG, OUTPUT);
  pinMode(FLOOD_ECHO, INPUT);

  // MQ-2
  pinMode(MQ2_DO, INPUT);

  // DHT22
  dht.begin();

  // Traffic buttons
  pinMode(BTN1, INPUT_PULLUP);
  pinMode(BTN2, INPUT_PULLUP);

  // Noise encoder
  pinMode(ENC_CLK, INPUT);
  pinMode(ENC_DT,  INPUT);
  pinMode(ENC_SW,  INPUT_PULLUP);
  lastCLK = digitalRead(ENC_CLK);

  // Street light
  pinMode(STREET_LED, OUTPUT);
  digitalWrite(STREET_LED, LOW);

  // Waste bin
  pinMode(BIN_TRIG, OUTPUT);
  pinMode(BIN_ECHO, INPUT);

  // Parking
  pinMode(PARK_TRIG_A, OUTPUT);
  pinMode(PARK_ECHO_A, INPUT);
  pinMode(PARK_TRIG_B, OUTPUT);
  pinMode(PARK_ECHO_B, INPUT);

  // Buzzer
  pinMode(BUZZER, OUTPUT);
  digitalWrite(BUZZER, LOW);

  Serial.println("================================");
  Serial.println("  URBAN SENTINEL IoT MONITOR   ");
  Serial.println("  All 10 Sensors Initialised   ");
  Serial.println("================================");
  Serial.println("Warming up sensors (2s)...");
  delay(2000);
  initialiseSensorState();
  Serial.println("System Ready!");
  Serial.println("Reporting every 10 seconds...");
  printDivider();
}

// =============================================
//   LOOP
// =============================================

void loop() {
  handleBuzzer();

  // ── Traffic buttons (every loop) ───────────
  bool btn1Now = digitalRead(BTN1);
  bool btn2Now = digitalRead(BTN2);
  if (btn1Now == LOW && btn1Prev == HIGH) lane1Count++;
  if (btn2Now == LOW && btn2Prev == HIGH) lane2Count++;
  btn1Prev = btn1Now;
  btn2Prev = btn2Now;

  // ── Noise encoder (every loop) ─────────────
  int currentCLK = digitalRead(ENC_CLK);
  if (currentCLK != lastCLK) {
    noiseLevel += (digitalRead(ENC_DT) != currentCLK) ? 5 : -5;
    noiseLevel = constrain(noiseLevel, 20, 130);
  }
  lastCLK = currentCLK;

  if (digitalRead(ENC_SW) == LOW) {
    noiseLevel = 40;
    delay(300);
  }

  // ── Report every 10 seconds ─────────────────
  if (millis() - lastReport >= REPORT_INTERVAL) {
    lastReport = millis();
    reportCount++;
    float dayPhase = fmodf(static_cast<float>(reportCount), 36.0f) / 36.0f;
    float dayWave = 0.5f + 0.5f * sinf((2.0f * PI * dayPhase) - (PI / 2.0f));
    float rushWave = 0.5f + 0.5f * sinf(4.0f * PI * dayPhase);

    // 1. Flood
    float floodReading = getDistance(FLOOD_TRIG, FLOOD_ECHO);
    float floodTarget = simFloodDist;
    if (simRainPct >= 70) {
      floodTarget -= randomFloat(2.0f, 5.5f);
    } else if (simRainPct >= 35) {
      floodTarget -= randomFloat(0.8f, 2.5f);
    } else {
      floodTarget += randomFloat(1.0f, 3.5f);
    }
    if (floodReading > 0.0f && floodReading < 160.0f) {
      floodTarget = clampFloat((floodTarget * 0.45f) + (floodReading * 0.55f), 5.0f, 100.0f);
    }
    simFloodDist = easeTowards(simFloodDist, floodTarget, 0.55f, 4.5f, 5.0f, 100.0f);
    float floodDist = simFloodDist;
    int   floodPct  = map(floodDist, 100, 5, 0, 100);
    floodPct        = constrain(floodPct, 0, 100);

    // 2. Air Quality
    int  smokeRaw     = analogRead(MQ2_AO);
    bool smokeDigital = digitalRead(MQ2_DO) == LOW;
    int  smokeTarget  = 8 + static_cast<int>(rushWave * 18.0f) + random(-3, 4);
    if (smokeSpikeTicks == 0 && chance(0.12f)) {
      smokeSpikeTicks = random(2, 5);
    }
    if (smokeSpikeTicks > 0) {
      smokeTarget += random(18, 42);
      smokeSpikeTicks--;
    }
    int smokeManual = constrain(map(smokeRaw, 0, 4095, 0, 100), 0, 100);
    if (smokeManual > 0) {
      smokeTarget = static_cast<int>((smokeTarget * 0.45f) + (smokeManual * 0.55f));
    }
    if (smokeDigital) {
      smokeTarget = max(smokeTarget, 85);
    }
    simSmokePct       = easeTowardsInt(simSmokePct, smokeTarget, 0.60f, 16, 0, 100);
    int  smokePct     = simSmokePct;

    // 3. Temperature & Humidity
    float temperatureReading = dht.readTemperature();
    float humidityReading    = dht.readHumidity();
    bool  dhtError           = isnan(temperatureReading) || isnan(humidityReading);
    float temperatureTarget = 22.5f + (dayWave * 10.5f) - (simRainPct * 0.05f) + randomFloat(-0.6f, 0.6f);
    if (!isnan(temperatureReading)) {
      temperatureTarget = (temperatureTarget * 0.55f) +
                          (clampFloat(temperatureReading, 18.0f, 50.0f) * 0.45f);
    }
    simTemperature = easeTowards(simTemperature, temperatureTarget, 0.45f, 1.4f, 18.0f, 50.0f);

    float humidityTarget = 42.0f + ((1.0f - dayWave) * 22.0f) + (simRainPct * 0.30f) + randomFloat(-2.0f, 2.0f);
    if (!isnan(humidityReading)) {
      humidityTarget = (humidityTarget * 0.55f) +
                       (clampFloat(humidityReading, 25.0f, 100.0f) * 0.45f);
    }
    simHumidity = easeTowards(simHumidity, humidityTarget, 0.35f, 4.0f, 25.0f, 100.0f);
    float temperature = simTemperature;
    float humidity    = simHumidity;

    // 4. Traffic
    float trafficTarget = 3.0f + (rushWave * 11.0f) + ((1.0f - dayWave) * 2.0f) + randomFloat(-1.5f, 2.0f);
    simTrafficFlow = easeTowards(simTrafficFlow, trafficTarget, 0.55f, 4.5f, 0.0f, 18.0f);
    int autoTraffic = static_cast<int>(roundf(simTrafficFlow));
    int autoLane1 = autoTraffic / 2 + (chance(0.35f) ? 1 : 0);
    int autoLane2 = max(0, autoTraffic - autoLane1);
    int lane1Vehicles = lane1Count + autoLane1;
    int lane2Vehicles = lane2Count + autoLane2;
    int totalVehicles = lane1Vehicles + lane2Vehicles;

    // 5. Noise
    int manualNoiseTarget = noiseLevel;
    int ambientNoiseTarget = 34 + static_cast<int>(simTrafficFlow * 2.2f) +
                             static_cast<int>(simRainPct * 0.10f) + random(-3, 4);
    noiseLevel = easeTowardsInt(
      noiseLevel,
      max(manualNoiseTarget, ambientNoiseTarget),
      0.45f, 7, 30, 110
    );

    // 6. Street Light
    int  ldrRaw      = analogRead(LDR_PIN);
    int  naturalLight = constrain(
      static_cast<int>(dayWave * 92.0f) - static_cast<int>(simRainPct * 0.20f) + random(-5, 6),
      3, 100
    );
    int  lightManual = constrain(map(ldrRaw, 0, 4095, 0, 100), 0, 100);
    int  lightTarget = static_cast<int>((naturalLight * 0.7f) + (lightManual * 0.3f));
    simLightPct      = easeTowardsInt(simLightPct, lightTarget, 0.60f, 14, 0, 100);
    int  lightPct    = simLightPct;
    bool isNight  = lightPct < 30;
    digitalWrite(STREET_LED, isNight ? HIGH : LOW);
    bool lightFault = isNight && digitalRead(STREET_LED) == LOW;

    // 7. Waste Bin
    float binReading = getDistance(BIN_TRIG, BIN_ECHO);
    float binFillTarget = distanceToFillPct(simBinDist) + randomFloat(1.0f, 4.0f);
    if (distanceToFillPct(simBinDist) > 92.0f && chance(0.30f)) {
      binFillTarget = randomFloat(8.0f, 22.0f);
    }
    if (binReading > 0.0f && binReading < 100.0f) {
      float manualFill = distanceToFillPct(clampFloat(binReading, BIN_FULL_CM, BIN_EMPTY_CM));
      binFillTarget = (binFillTarget * 0.45f) + (manualFill * 0.55f);
    }
    float nextFill = easeTowards(
      distanceToFillPct(simBinDist), binFillTarget, 0.55f, 8.0f, 0.0f, 100.0f
    );
    simBinDist = fillPctToDistance(nextFill);
    float binDist = simBinDist;
    int   binPct  = map(binDist, BIN_EMPTY_CM, BIN_FULL_CM, 0, 100);
    binPct        = constrain(binPct, 0, 100);

    // 8. Rain
    int  ntcRaw         = analogRead(NTC_PIN);
    int  ntcManualPct   = 0;
    int  ntcManualTemp  = constrain(map(ntcRaw, 0, 4095, 50, -10), -10, 50);
    if (ntcManualTemp < 20) {
      ntcManualPct = constrain(map(ntcManualTemp, 20, -10, 0, 100), 0, 100);
    }
    if (rainEpisodeTicks == 0 && chance(0.10f)) {
      rainEpisodeTicks = random(3, 8);
    }
    int rainTargetPct = 0;
    if (rainEpisodeTicks > 0) {
      rainTargetPct = random(35, 95);
      rainEpisodeTicks--;
    }
    rainTargetPct = max(rainTargetPct, ntcManualPct);
    simRainPct = easeTowardsInt(simRainPct, rainTargetPct, 0.55f, 18, 0, 100);
    int weatherRainTemp = static_cast<int>(roundf(temperature - (simRainPct * 0.08f)));
    int rainTempTarget = static_cast<int>((weatherRainTemp * 0.7f) + (ntcManualTemp * 0.3f));
    simRainTemp = easeTowardsInt(simRainTemp, rainTempTarget, 0.35f, 3, -10, 50);
    int  ntcTemp        = simRainTemp;
    bool rainDetected   = simRainPct > 0;
    int  rainPct        = 0;
    if (rainDetected) {
      rainPct = simRainPct;
    }

    // 9. Fire
    bool fireConfirmed = smokePct > 80 || smokeDigital;
    bool heavySmoke    = smokePct > 60 && smokePct <= 80;

    // 10. Parking
    float parkReadingA = getDistance(PARK_TRIG_A, PARK_ECHO_A);
    float parkReadingB = getDistance(PARK_TRIG_B, PARK_ECHO_B);
    bool manualASeen = parkReadingA > 0.0f && parkReadingA < 120.0f;
    bool manualBSeen = parkReadingB > 0.0f && parkReadingB < 120.0f;
    if (manualASeen) {
      simSpotAOccupied = parkReadingA < CAR_PRESENT_CM;
    } else if (simSpotAOccupied) {
      if (chance(0.18f)) simSpotAOccupied = false;
    } else if (chance(clampFloat((simTrafficFlow + 2.0f) / 26.0f, 0.08f, 0.55f))) {
      simSpotAOccupied = true;
    }
    if (manualBSeen) {
      simSpotBOccupied = parkReadingB < CAR_PRESENT_CM;
    } else if (simSpotBOccupied) {
      if (chance(0.16f)) simSpotBOccupied = false;
    } else if (chance(clampFloat((simTrafficFlow + 1.0f) / 28.0f, 0.08f, 0.50f))) {
      simSpotBOccupied = true;
    }
    float parkTargetA = simSpotAOccupied ? randomFloat(7.0f, 15.0f) : randomFloat(34.0f, 70.0f);
    float parkTargetB = simSpotBOccupied ? randomFloat(7.0f, 16.0f) : randomFloat(36.0f, 72.0f);
    if (manualASeen) parkTargetA = parkReadingA;
    if (manualBSeen) parkTargetB = parkReadingB;
    simParkDistA = easeTowards(simParkDistA, parkTargetA, 0.65f, 10.0f, 3.0f, 120.0f);
    simParkDistB = easeTowards(simParkDistB, parkTargetB, 0.65f, 10.0f, 3.0f, 120.0f);
    float distA         = simParkDistA;
    float distB         = simParkDistB;
    bool  spotAOccupied = distA > 0 && distA < CAR_PRESENT_CM;
    bool  spotBOccupied = distB > 0 && distB < CAR_PRESENT_CM;

    if (spotAOccupied && !spotAWasOccupied)
      spotAOccupiedSince = millis();
    if (spotBOccupied && !spotBWasOccupied)
      spotBOccupiedSince = millis();
    spotAWasOccupied = spotAOccupied;
    spotBWasOccupied = spotBOccupied;

    bool spotAIllegal = spotAOccupied &&
      (millis() - spotAOccupiedSince >= ILLEGAL_PARK_MS);
    bool spotBIllegal = spotBOccupied &&
      (millis() - spotBOccupiedSince >= ILLEGAL_PARK_MS);
    int availableSpots = (!spotAOccupied ? 1 : 0) +
                         (!spotBOccupied ? 1 : 0);

    // Trigger alarms
    if (fireConfirmed || floodPct > 80) triggerAlarm();

    // ── PRINT FULL REPORT ─────────────────────
    Serial.println("\n");
    printDivider();
    Serial.println("  URBAN SENTINEL - FULL REPORT  ");
    printDivider();

    // 1. Flood
    Serial.println("FLOOD / WATER LEVEL");
    Serial.print("  Distance : ");
    Serial.print(floodDist, 1);
    Serial.println(" cm");
    Serial.print("  Level    : ");
    Serial.print(floodPct);
    Serial.println("%");
    if (floodPct > 80)
      Serial.println("  Status   : CRITICAL - FLOOD RISK!");
    else if (floodPct > 50)
      Serial.println("  Status   : WARNING - Rising Water");
    else
      Serial.println("  Status   : NORMAL");
    printDivider();

    // 2. Air Quality
    Serial.println("AIR QUALITY");
    Serial.print("  Smoke    : ");
    Serial.print(smokePct);
    Serial.println("%");
    if (smokePct > 70)
      Serial.println("  Status   : POOR - Hazardous!");
    else if (smokePct > 40)
      Serial.println("  Status   : MODERATE");
    else
      Serial.println("  Status   : GOOD");
    printDivider();

    // 3. Temperature & Humidity
    Serial.println("TEMPERATURE & HUMIDITY");
    Serial.print("  Temp     : ");
    Serial.print(temperature);
    Serial.println(" C");
    Serial.print("  Humidity : ");
    Serial.print(humidity);
    Serial.println("%");
    if (dhtError)
      Serial.println("  Note     : LIVE SENSOR MISSED, USING DRIFTED VALUE");
    if (temperature > 45)
      Serial.println("  Status   : CRITICAL - Extreme Heat!");
    else if (humidity > 90)
      Serial.println("  Status   : WARNING - Very High Humidity!");
    else
      Serial.println("  Status   : NORMAL");
    printDivider();

    // 4. Traffic
    Serial.println("TRAFFIC MONITOR");
    Serial.print("  Lane 1   : ");
    Serial.println(lane1Vehicles);
    Serial.print("  Lane 2   : ");
    Serial.println(lane2Vehicles);
    Serial.print("  Total    : ");
    Serial.println(totalVehicles);
    if (totalVehicles > 16)
      Serial.println("  Status   : HIGH TRAFFIC - Congestion!");
    else if (totalVehicles > 8)
      Serial.println("  Status   : MODERATE TRAFFIC");
    else
      Serial.println("  Status   : LOW TRAFFIC");
    lane1Count = 0;
    lane2Count = 0;
    printDivider();

    // 5. Noise
    Serial.println("NOISE POLLUTION");
    Serial.print("  Level    : ");
    Serial.print(noiseLevel);
    Serial.println(" dB");
    if (noiseLevel > 85)
      Serial.println("  Status   : CRITICAL - Harmful!");
    else if (noiseLevel > 70)
      Serial.println("  Status   : HIGH - Disturbing");
    else if (noiseLevel > 50)
      Serial.println("  Status   : MODERATE");
    else
      Serial.println("  Status   : QUIET - Normal");
    printDivider();

    // 6. Street Light
    Serial.println("STREET LIGHT");
    Serial.print("  Light    : ");
    Serial.print(lightPct);
    Serial.println("%");
    Serial.print("  Time     : ");
    Serial.println(isNight ? "NIGHT" : "DAY");
    if (lightFault)
      Serial.println("  Status   : FAULT - Light should be ON!");
    else
      Serial.println("  Status   : WORKING NORMALLY");
    printDivider();

    // 7. Waste Bin
    Serial.println("WASTE BIN");
    Serial.print("  Distance : ");
    Serial.print(binDist, 1);
    Serial.println(" cm");
    Serial.print("  Fill     : ");
    Serial.print(binPct);
    Serial.println("%");
    if (binPct >= 95)
      Serial.println("  Status   : FULL - Immediate Collection!");
    else if (binPct >= 80)
      Serial.println("  Status   : NEARLY FULL - Schedule Soon");
    else if (binPct >= 40)
      Serial.println("  Status   : HALF FULL");
    else
      Serial.println("  Status   : EMPTY - OK");
    printDivider();

    // 8. Rain
    Serial.println("RAIN MONITOR");
    Serial.print("  Temp     : ");
    Serial.print(ntcTemp);
    Serial.println(" C");
    Serial.print("  Rain     : ");
    Serial.print(rainPct);
    Serial.println("%");
    if (rainPct > 90)
      Serial.println("  Status   : CRITICAL - Extreme Rain!");
    else if (rainPct > 70)
      Serial.println("  Status   : WARNING - Heavy Rain!");
    else if (rainPct > 40)
      Serial.println("  Status   : MODERATE RAIN");
    else if (rainDetected)
      Serial.println("  Status   : LIGHT DRIZZLE");
    else
      Serial.println("  Status   : NO RAIN");
    printDivider();

    // 9. Fire & Smoke
    Serial.println("FIRE & SMOKE");
    Serial.print("  Smoke    : ");
    Serial.print(smokePct);
    Serial.println("%");
    if (fireConfirmed)
      Serial.println("  Status   : CRITICAL - FIRE CONFIRMED!");
    else if (heavySmoke)
      Serial.println("  Status   : WARNING - Heavy Smoke!");
    else if (smokePct > 30)
      Serial.println("  Status   : CAUTION - Smoke Detected");
    else
      Serial.println("  Status   : ALL CLEAR");
    printDivider();

    // 10. Parking
    Serial.println("SMART PARKING");
    Serial.print("  Spot A   : ");
    Serial.println(spotAIllegal ? "ILLEGAL PARKING!" :
                   spotAOccupied ? "OCCUPIED" : "AVAILABLE");
    Serial.print("  Spot B   : ");
    Serial.println(spotBIllegal ? "ILLEGAL PARKING!" :
                   spotBOccupied ? "OCCUPIED" : "AVAILABLE");
    Serial.print("  Available: ");
    Serial.print(availableSpots);
    Serial.println(" / 2");
    if (availableSpots == 0)
      Serial.println("  Status   : PARKING FULL!");
    else
      Serial.println("  Status   : SPOTS AVAILABLE");
    printDivider();
    Serial.println("  END OF REPORT              ");
    printDivider();
    Serial.println();
  }

  delay(50);
}
