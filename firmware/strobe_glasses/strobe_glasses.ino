#include <Arduino.h>
#include <avr/eeprom.h>
#include <avr/interrupt.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <util/atomic.h>

#if !defined(__AVR_ATtiny402__) || F_CPU != 5000000UL
#error "Select ATtiny402 and 5 MHz internal."
#endif
#if !defined(MILLIS_USE_TIMERA0) && !defined(MILLIS_USE_TIMERNONE)
#error "Use the default ATtiny402 millis timer (TCA0) or disable millis."
#endif

// MK1: PA0 stays dedicated to UPDI. The charge LED has no MCU connection.
constexpr uint8_t LensPins = PIN1_bm | PIN2_bm | PIN6_bm | PIN7_bm;
constexpr uint8_t ButtonPin = PIN3_bm;

constexpr uint8_t Rates[] = {2, 4, 5, 6, 8, 10, 15, 20};
constexpr uint8_t DutySteps = 7;  // 20% through 80%, in 10-point steps
constexpr uint8_t Custom = 3;
constexpr uint16_t HoldMs = 800;
constexpr uint8_t DebounceMs = 25;
constexpr uint16_t DoubleTapMs = 300;
constexpr uint16_t EditPauseMs = 600;

struct Tuning {
  uint8_t rateIndex;
  uint8_t dutyIndex;
};

constexpr Tuning Presets[] = {
  {3, 2},  // Light: 6 fps, 40% dark
  {2, 3},  // Balanced: 5 fps, 50% dark
  {1, 4},  // Heavy: 4 fps, 60% dark
};

enum class Mode : uint8_t { Clear, Playing, AdjustRate, AdjustDuty };
// Two GPIO bits per eye: 00 shorts the electrodes, 01 and 10 drive the LCD.
enum class Phase : uint8_t { Clear = 0, Positive = 1, Negative = 2 };

struct FrameTiming {
  uint16_t clearMs;
  uint8_t pairs;
  uint8_t halfMs;
  uint8_t longerPairs;
  uint8_t rightDelayMs;
};

// Byte 0 keeps the original preset/rate/duty encoding. An erased byte 1
// selects together mode on both a fresh chip and an existing MK1.
uint8_t EEMEM savedSettings[2] = {0xff, 0xff};
bool alternating = false;
uint8_t selectedPreset = 0;
Tuning custom = Presets[1];
Tuning draft;
Mode mode = Mode::Clear;
bool previewPaused = false;
uint16_t pauseStartedMs = 0;

bool rawPressed = false;
bool pressed = false;
bool holdHandled = false;
uint16_t buttonChangedMs = 0;
uint16_t pressStartedMs = 0;
bool tapPending = false;
uint16_t tapReleasedMs = 0;

volatile uint16_t ticksMs = 0;
volatile FrameTiming requested = {};  // zero pairs requests clear
volatile bool timingChanged = false;
FrameTiming active;

struct Eye {
  Phase phase;
  uint16_t remainingMs;
  uint8_t pairsLeft;
  uint8_t longerPairs;
  uint8_t pairHalfMs;
};
Eye leftEye = {}, rightEye = {};

void tickEye(Eye &eye, bool stopping) {
  if (stopping && eye.phase == Phase::Clear) return;
  if (--eye.remainingMs) return;
  switch (eye.phase) {
    case Phase::Clear:
      eye.pairsLeft = active.pairs;
      eye.longerPairs = active.longerPairs;
      break;
    case Phase::Positive:
      eye.phase = Phase::Negative;
      eye.remainingMs = eye.pairHalfMs;
      return;
    case Phase::Negative:
      if (stopping || --eye.pairsLeft == 0) {
        eye.phase = Phase::Clear;
        eye.remainingMs = active.clearMs;
        return;
      }
      break;
  }
  eye.pairHalfMs = active.halfMs;
  if (eye.longerPairs) {
    ++eye.pairHalfMs;
    --eye.longerPairs;
  }
  eye.phase = Phase::Positive;
  eye.remainingMs = eye.pairHalfMs;
}

ISR(TCB0_INT_vect) {
  TCB0.INTFLAGS = TCB_CAPT_bm;
  ++ticksMs;
  // Finish each eye's current AC pair before restarting the two envelopes.
  if (timingChanged && leftEye.phase == Phase::Clear && rightEye.phase == Phase::Clear) {
    active = {requested.clearMs, requested.pairs, requested.halfMs,
              requested.longerPairs, requested.rightDelayMs};
    leftEye.remainingMs = 1;
    rightEye.remainingMs = 1 + active.rightDelayMs;
    timingChanged = false;
  }
  if (!active.pairs) return;
  tickEye(leftEye, timingChanged);
  tickEye(rightEye, timingChanged);
  // J3 uses PA1/PA2 and J4 uses PA6/PA7. Update all electrodes together.
  VPORTA.OUT = (VPORTA.OUT & ~LensPins) | (uint8_t(leftEye.phase) << 1)
               | (uint8_t(rightEye.phase) << 6);
}

Tuning selectedTuning() {
  return selectedPreset == Custom ? custom : Presets[selectedPreset];
}

void updateTiming() {
  FrameTiming timing = {};
  if (mode != Mode::Clear && !previewPaused) {
    const Tuning tuning = mode == Mode::Playing ? selectedTuning() : draft;
    const uint8_t fps = Rates[tuning.rateIndex];
    const uint8_t duty = 20 + 10 * tuning.dutyIndex;
    const uint16_t frameMs = (1000 + fps / 2) / fps;
    // Round to an even number of milliseconds and divide the dark window
    // into complete pairs near 100 Hz. Each pair has equal +/- durations.
    const uint16_t darkHalfMs = (frameMs * duty + 100) / 200;
    timing.clearMs = frameMs - 2 * darkHalfMs;
    timing.pairs = (darkHalfMs + 2) / 5;
    timing.halfMs = darkHalfMs / timing.pairs;
    timing.longerPairs = darkHalfMs % timing.pairs;
    timing.rightDelayMs = alternating ? frameMs / 2 : 0;
  }
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    requested.clearMs = timing.clearMs;
    requested.pairs = timing.pairs;
    requested.halfMs = timing.halfMs;
    requested.longerPairs = timing.longerPairs;
    requested.rightDelayMs = timing.rightDelayMs;
    timingChanged = true;
  }
}

void loadSettings() {
  alternating = eeprom_read_byte(&savedSettings[1]) == 1;
  const uint8_t settings = eeprom_read_byte(&savedSettings[0]);
  const uint8_t dutyIndex = settings & 0x07;
  if (dutyIndex >= DutySteps) return;  // Includes erased EEPROM (0xff).
  selectedPreset = settings >> 6;
  custom = {uint8_t((settings >> 3) & 0x07), dutyIndex};
}

void saveSettings() {
  eeprom_update_byte(&savedSettings[0],
                     (selectedPreset << 6) | (custom.rateIndex << 3) | custom.dutyIndex);
}

void tap() {
  switch (mode) {
    case Mode::Clear:
      mode = Mode::Playing;
      break;
    case Mode::Playing:
      selectedPreset = (selectedPreset + 1) % (Custom + 1);
      saveSettings();
      break;
    case Mode::AdjustRate:
      draft.rateIndex = (draft.rateIndex + 1) % sizeof(Rates);
      break;
    case Mode::AdjustDuty:
      draft.dutyIndex = (draft.dutyIndex + 1) % DutySteps;
      break;
  }
  updateTiming();
}

void hold(uint16_t now) {
  switch (mode) {
    case Mode::Playing:
      mode = Mode::Clear;
      break;
    case Mode::Clear:
      draft = selectedTuning();
      mode = Mode::AdjustRate;
      break;
    case Mode::AdjustRate:
      mode = Mode::AdjustDuty;
      previewPaused = true;
      pauseStartedMs = now;
      break;
    case Mode::AdjustDuty:
      custom = draft;
      selectedPreset = Custom;
      mode = Mode::Playing;
      previewPaused = true;
      pauseStartedMs = now;
      saveSettings();
      break;
  }
  updateTiming();
}

void readButton(uint16_t now) {
  if (tapPending && !pressed && !rawPressed && uint16_t(now - tapReleasedMs) >= DoubleTapMs) {
    tapPending = false;
    tap();
  }
  const bool down = !(VPORTA.IN & ButtonPin);
  if (down != rawPressed) {
    rawPressed = down;
    buttonChangedMs = now;
  }
  if (rawPressed != pressed && uint16_t(now - buttonChangedMs) >= DebounceMs) {
    pressed = rawPressed;
    if (pressed) {
      pressStartedMs = now;
      holdHandled = false;
    } else if (!holdHandled) {
      if (mode != Mode::Playing) {
        tap();
      } else if (tapPending) {
        tapPending = false;
        alternating = !alternating;
        updateTiming();
        eeprom_update_byte(&savedSettings[1], alternating);
      } else {
        tapPending = true;
        tapReleasedMs = now;
      }
    }
  }
  if (pressed && rawPressed && !holdHandled && uint16_t(now - pressStartedMs) >= HoldMs) {
    holdHandled = true;
    tapPending = false;
    hold(now);
  }
}

void setup() {
  PORTA.OUTCLR = LensPins;
  PORTA.DIRSET = LensPins;
  PORTA.PIN3CTRL = PORT_PULLUPEN_bm;
  rawPressed = pressed = holdHandled = !(VPORTA.IN & ButtonPin);
  loadSettings();

  // The sketch uses TCB0 for all timing. Stop the core's default TCA0 tick.
  TCA0.SINGLE.CTRLA = 0;
  TCA0.SPLIT.INTCTRL = 0;
  TCB0.CTRLA = 0;
  TCB0.CTRLB = TCB_CNTMODE_INT_gc;
  TCB0.CCMP = F_CPU / 2 / 1000 - 1;
  TCB0.CNT = 0;
  TCB0.INTFLAGS = TCB_CAPT_bm;
  TCB0.INTCTRL = TCB_CAPT_bm;
  TCB0.CTRLA = TCB_CLKSEL_CLKDIV2_gc | TCB_ENABLE_bm;
  set_sleep_mode(SLEEP_MODE_IDLE);
  wdt_reset();
  _PROTECTED_WRITE(WDT.CTRLA, WDT_PERIOD_1KCLK_gc);
}

void loop() {
  static uint16_t lastTick = 0;
  uint16_t now;
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    now = ticksMs;
  }
  if (now != lastTick) {
    lastTick = now;
    wdt_reset();
    readButton(now);
    if (previewPaused && uint16_t(now - pauseStartedMs) >= EditPauseMs) {
      previewPaused = false;
      updateTiming();
    }
  }
  sleep_mode();
}
