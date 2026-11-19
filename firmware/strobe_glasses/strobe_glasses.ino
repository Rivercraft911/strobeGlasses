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
constexpr uint8_t PositivePins = PIN1_bm | PIN6_bm;
constexpr uint8_t NegativePins = PIN2_bm | PIN7_bm;
constexpr uint8_t LensPins = PositivePins | NegativePins;
constexpr uint8_t ButtonPin = PIN3_bm;

constexpr uint8_t Rates[] = {2, 4, 5, 6, 8, 10, 15, 20};
constexpr uint8_t DutySteps = 7;  // 20% through 80%, in 10-point steps
constexpr uint8_t Custom = 3;
constexpr uint16_t HoldMs = 800;
constexpr uint8_t DebounceMs = 25;
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
enum class Phase : uint8_t { Clear, Positive, Negative };

struct FrameTiming {
  uint16_t clearMs;
  uint8_t pairs;
  uint8_t halfMs;
  uint8_t longerPairs;
};

// All edits live in RAM until saved. The selected slot and custom values fit
// in one EEPROM byte: two preset bits, three rate bits, three duty bits.
uint8_t EEMEM savedSettings = 0xff;
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

volatile uint16_t ticksMs = 0;
volatile FrameTiming requested = {};  // zero pairs requests clear
Phase phase = Phase::Clear;
uint16_t phaseLeftMs = 1;
FrameTiming active;
uint8_t pairHalfMs;

void setLensPins(uint8_t pins) {
  VPORTA.OUT = (VPORTA.OUT & ~LensPins) | pins;
}

void startPair() {
  pairHalfMs = active.halfMs;
  if (active.longerPairs) {
    ++pairHalfMs;
    --active.longerPairs;
  }
  setLensPins(PositivePins);
  phase = Phase::Positive;
  phaseLeftMs = pairHalfMs;
}

ISR(TCB0_INT_vect) {
  TCB0.INTFLAGS = TCB_CAPT_bm;
  ++ticksMs;
  if (--phaseLeftMs) return;

  switch (phase) {
    case Phase::Clear:
      if (!requested.pairs) {
        phaseLeftMs = 1;
        return;
      }
      active = {requested.clearMs, requested.pairs,
                requested.halfMs, requested.longerPairs};
      startPair();
      break;
    case Phase::Positive:
      setLensPins(NegativePins);
      phase = Phase::Negative;
      phaseLeftMs = pairHalfMs;
      break;
    case Phase::Negative:
      if (requested.pairs && --active.pairs) {
        startPair();
      } else {
        setLensPins(0);
        phase = Phase::Clear;
        phaseLeftMs = requested.pairs ? active.clearMs : 1;
      }
      break;
  }
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
  }
  ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
    requested.clearMs = timing.clearMs;
    requested.pairs = timing.pairs;
    requested.halfMs = timing.halfMs;
    requested.longerPairs = timing.longerPairs;
  }
}

void loadSettings() {
  const uint8_t settings = eeprom_read_byte(&savedSettings);
  const uint8_t dutyIndex = settings & 0x07;
  if (dutyIndex >= DutySteps) return;  // Includes erased EEPROM (0xff).
  selectedPreset = settings >> 6;
  custom = {uint8_t((settings >> 3) & 0x07), dutyIndex};
}

void saveSettings() {
  eeprom_update_byte(&savedSettings,
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
      tap();
    }
  }
  if (pressed && rawPressed && !holdHandled && uint16_t(now - pressStartedMs) >= HoldMs) {
    holdHandled = true;
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
