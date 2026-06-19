/* Compile for Nano Every
 * Nano Every is found in Mega2560 boards
 */

/*
This file includes lines in preparation for the IV-mux motherboard v2.0
These are tagged with V2P0

*/
 
#include <avr/sleep.h>

// For Nano Every port definitions, see C:\Program Files (x86)\Arduino\hardware\tools\avr\avr\include\avr\iom4809.h

/*  Attempt to get it into low power state most of the time to reduce cooling requirements in vacuum
 *  - It didn't work
 *  - when trying to compile it later, the register accesses in the set_low_power routine failed 
 *  to compile in spite of setting AtMEGA328 emulation (although they had compiled previously)
 *  
 *  ... so the code is #defined out
*/
#define LOWPOWER_SLEEP 0
#define CTRL_C 3

// Macro to return number of elements in an array
#define COUNT_OF(x) ((sizeof(x) / sizeof(0 [x])) / ((size_t)(!(sizeof(x) % sizeof(0 [x])))))

// When undefined, compile for IV mux
// When defined, compile for IV-pulse mux
#define IVPULSEMUX

#ifdef IVPULSEMUX

// relay setup parameters
const int boardCount = 4;                           // how many boards are supported
const int channelsPerBoard = 24;                    // how many channels per board
const int maxChan = boardCount * channelsPerBoard;  // number of channels

// shift register (MIC5891) control pinout
int serPins[boardCount] = { 2, 3, 4, 5 };

// This is a hack to make the motherboard V1.0 work to address more than one daughterboard
// By mistake, a single IV_ON was designated on the microcontroller, and distributed to all boards
// instead of 4 of them, one distributed to each of the boards.
// Instead we used THERM1 - THERM4, and bridged each THERMn to the respective IV_ON pin, on the motherboard 
// (and also cut the IV_ON trace tying them all together)
int iv_on_pins[boardCount] = { A0, A1, A2, A3 };  

// V2P0 - new version for when these pins are connected
// Delete above version of iv_on_pins definition
//int iv_on_pins[boardCount] = { 6, 7, 8, 13 };  

const int SRCLK = 9;   // serial clock
const int RCLK = 10;   // strobe to active register
const int SRCLR = 11;  // asynchronous clear (active low)

//const int IV_ON = 13;  // DELETE ME
const int OE = 11;

const int BYPASS = 12;  // TEMPORARY - it shouldn't have been connected to pin 12!

#else

// relay pi parameters
const int boardCount = 6;                           // how many boards are supported
const int channelsPerBoard = 15;                    // how many channels per board
const int maxChan = boardCount * channelsPerBoard;  // number of channels
const int senseRelayBit = 15;                       // position of sense relay bit

// shift register (74HC595) control pinout
int serPins[boardCount] = { 2, 3, 4, 5, 6, 7 };
const int SRCLK = 9;   // serial clock
const int RCLK = 10;   // strobe to active register
const int SRCLR = 11;  // asynchronous clear (active low)

#endif

// For synchronization with IV curves using falling voltage transition
// Note: not on rev 1.0 PCB
const int SYNC_PULSE = 8;  // for sensing sync pulse - stealing last board select pin, for now

HardwareSerial *control;
HardwareSerial *debug;

const int inbuflen = 80;
char inbuf[inbuflen];
int charsInBuf;

/*
Look for the first port that receives 'g' and use it for control and debug
*/
void SetPort() {
  Serial.begin(9600);
  Serial1.begin(9600);

#define AUTO // auto select based on 'g'

#ifdef AUTO

  while(1)
  {
    int c;

    c = Serial.read();
    if ('g'== c) {
      control = debug = &Serial;
      debug->println("Serial chosen\n");
      break;
    }

    c = Serial1.read();
    if ('g'== c) {
      control = debug = &Serial1;
      debug->println("Serial1 chosen\n");
      break;
    }
  }

#else

// hard coded port
control = debug = &Serial1; // or &Serial

#endif

  control->print("MUX control interface\n\n");
}


void setup() {
  int i;

  //SetPort();

  for (i = 0; i < boardCount; i++) {
    pinMode(serPins[i], OUTPUT);
#ifdef IVPULSEMUX
    digitalWrite(iv_on_pins[i], LOW);
    pinMode(iv_on_pins[i], OUTPUT);
#endif
  }

// TEMPORARY
#ifdef IVPULSEMUX
  pinMode(BYPASS, OUTPUT);
  digitalWrite(BYPASS, LOW);
#endif

  pinMode(SRCLK, OUTPUT);
  pinMode(RCLK, OUTPUT);

#ifdef IVPULSEMUX
#else
  pinMode(SRCLR, OUTPUT);
#endif

  digitalWrite(SRCLK, LOW);
  digitalWrite(RCLK, LOW);

#ifdef IVPULSEMUX
  digitalWrite(OE, HIGH);  // high is inactive
  pinMode(OE, OUTPUT);
#else
  digitalWrite(SRCLR, HIGH);
#endif
  pinMode(SYNC_PULSE, INPUT_PULLUP);

  charsInBuf = 0;
  zeroState();
  writeState();

#ifdef IVPULSEMUX
  // after the shift registers are all initialized, enable the outputs
  digitalWrite(OE, LOW);  // low is active
#endif

#if LOWPOWER_SLEEP
  set_low_power();
#endif

  SetPort();

}

void loop() {
  int c;
#if LOWPOWER_SLEEP
  sleep();  // wake on UART interrupt
#endif
  // read a character
  c = control->read();
  if (-1 == c) return;

  // add it to the buffer, if there's room
  if (charsInBuf < COUNT_OF(inbuf))
    inbuf[charsInBuf++] = c;

#define DELIMS " \n\r"
  // separate into command and arguments
  char *command, *arg1, *arg2, *arg3;
  if (c == '\n' || c == '\r') {
    if (inbuf[charsInBuf - 1] == '\n') inbuf[--charsInBuf] = 0;
    if (inbuf[charsInBuf - 1] == '\r') inbuf[--charsInBuf] = 0;
    debug->print("Command: <");
    debug->print(inbuf);
    debug->println(">");
    command = strtok(inbuf, DELIMS);
    arg1 = strtok(NULL, DELIMS);
    arg2 = strtok(NULL, DELIMS);
    arg3 = strtok(NULL, DELIMS);
  } else
    return;

  int status = -1;

  // "a" activate command
  // activate just one channel, with its bias and sense relays
  if (0 == strcasecmp(command, "a")) {
    debug->println("Activating");
    int chan = atoi(arg1);
    status = channelActive(chan);
  }


// This bypass function only works on Rev 1
/* #ifdef IVPULSEMUX
  // "y" activate bYpass line if uppercase, deactivate if lowercase
  else if (0 == strcmp(command, "Y")) {
    debug->println("Activating bypass");
    digitalWrite(BYPASS, HIGH);
    status = 0;
  }

  else if (0 == strcmp(command, "y")) {
    debug->println("Deactivating bypass");
    digitalWrite(BYPASS, LOW);
    status = 0;
  }
#endif
 */
 
  // "t" temperature read command
  else if (0 == strcasecmp(command, "t")) {
    tempRead();
    status = 0;
  }

  // "s" sense relay command
  // set state of sense relay on board of specified channel: s c 1/0
  else if (0 == strcasecmp(command, "s")) {
    debug->println("Sense");
    int chan = atoi(arg1);
    int state = atoi(arg2);
    status = setSenseRelayState(chan, state);
#ifndef IVPULSEMUX
    writeState();
#endif
  }

  // "b" bias relay command
  // set state of bias  relay on specified board and channel: s c 1/0
  else if (0 == strcasecmp(command, "b")) {
    debug->println("Bias");
    int chan = atoi(arg1);
    int state = atoi(arg2);
    status = setBiasRelayState(chan, state);
    writeState();
  }

#ifndef IVPULSEMUX
  // "q" seQuence command
  // run through a range of channels, activating one at a time, for specified time (mS)
  else if (0 == strcasecmp(command, "q")) {
    debug->println("Sequence");
    int from = atoi(arg1);
    int to = atoi(arg2);
    unsigned long ms = atol(arg3);
    status = sequence(from, to, ms);
  }
#endif
  // "d" dump command
  // dump state
  else if (0 == strcasecmp(command, "d")) {
    debug->println("Dump");
    dumpState();
    status = 0;
  }

  // "w" write command
  // write state to relays
  else if (0 == strcasecmp(command, "w")) {
    debug->println("Write");
    writeState();
    status = 0;
  }

  // "z" zero state command
  // zero state
  else if (0 == strcasecmp(command, "z")) {
    debug->println("Zero");
    zeroState();
    writeState();
    status = 0;
  }

  // "p" powerdown command
  else if (0 == strcasecmp(command, "p")) {
    debug->println("Sleeping...");
    delay(1000);
    //debug->println("After ...");
    lpsleep();
    status = 0;
  }

  else if (*inbuf == 0) {
    printHelp();
    status = 0;  // no error on null command
  } else {
    printHelp();
  }

  if (status)
    debug->println("Error in command");
  else
    debug->println("Command complete");

  charsInBuf = 0;
}

#if LOWPOWER_SLEEP
// disable some unused peripherals
void set_low_power() {
  // Disable the ADC by setting the ADEN bit (bit 7)  of the
  // ADCSRA register to zero.
  ADCSRA &= ~0x80;  // B01111111;

  // Disable the analog comparator by setting the ACD bit
  // (bit 7) of the ACSR register to one.
  ACSR |= 0x80;  // B10000000;

  // Disable digital input buffers on all analog input pins
  // by setting bits 0-5 of the DIDR0 register to one.
  // Of course, only do this if you are not using the analog
  // inputs for your project.
  // DIDR0 = DIDR0 | B00111111; // not sure about this one
}

void sleep() {
  sleep_enable();
  set_sleep_mode(SLEEP_MODE_IDLE);
  sleep_cpu();
}

#endif

void lpsleep(){
  sleep_enable();
  set_sleep_mode(SLEEP_MODE_PWR_DOWN);
  sleep_cpu();
}

// An array of 16-bit words, one for each board (SER pin)
// active high
// bit 0 = ON0 .. bit 14 = ON14 .. bit 15 = SENSE_ON
#ifdef IVPULSEMUX
uint32_t outState[boardCount];
#else
uint16_t outState[boardCount];
#endif

int channelActive(int chan) {
  zeroState();
  if (setBiasRelayState(chan, true)) return -1;
  if (setSenseRelayState(chan, true)) return -1;
  writeState();
  return 0;
}

const unsigned long MIN_PULSE = 500;  // 500uS

int sequence(int from, int to, long mSdelay) {
  int i;
  bool abort = false;
  if (from < 1 || to < 1 || from > to)
    return -1;
  for (i = from; i <= to && !abort; i++) {

    debug->print("Activating ");
    debug->print(i);
    debug->print(", at ");
    debug->println(millis());

    if (channelActive(i)) return -1;  // activate channel; abort on error exit

    // for positive delay parameter, just delay
    if (mSdelay >= 0)
      delay(mSdelay);
    else {
      // for negative delay parameter, first find a (long enough) negative-going pulse on the sync line
      bool done = false;
      while (!done && !abort) {
        while (HIGH == digitalRead(SYNC_PULSE))
          if (abort |= control->read() == CTRL_C) break;
        unsigned long start = micros();
        while (LOW == digitalRead(SYNC_PULSE))
          if (abort |= control->read() == CTRL_C) break;
        unsigned long width = micros() - start;
        done = width >= MIN_PULSE;
        debug->print("Pulse width: ");
        debug->println(width);
      }

      delay(-mSdelay);
    }
  }
  zeroState();
  writeState();
  return 0;
}

void writeState() {
  int i, j;
#ifdef IVPULSEMUX
  uint32_t mask = 0x800000;
#else
  uint16_t mask = 0x8000;
#endif
  for (i = 0; mask; i++, mask >>= 1) {
    // set SER pins
    for (j = 0; j < boardCount; j++)
      digitalWrite(serPins[j], 0 != (outState[j] & mask) ? HIGH : LOW);

    // clock '595 shift register
    digitalWrite(SRCLK, HIGH);
    digitalWrite(SRCLK, LOW);
  }

  // update '595 output register
  digitalWrite(RCLK, HIGH);
  digitalWrite(RCLK, LOW);
}

void zeroState() {
  int i;
  for (i = 0; i < boardCount; i++) {
    outState[i] = 0;
    digitalWrite(iv_on_pins[i], LOW);
  }
}

void dumpState() {
  int i;
  for (i = 0; i < boardCount; i++)
    debug->println(outState[i], HEX);
}

int setBiasRelayState(uint16_t channel, bool enable) {
  if (channel < 1 || channel > maxChan) return -1;

  int board = (channel - 1) / channelsPerBoard;
  int chanOnBoard = (channel - 1) % channelsPerBoard;

  if (enable)
    bitSet(outState[board], chanOnBoard);
  else
    bitClear(outState[board], chanOnBoard);

  return 0;
}

int setSenseRelayState(uint16_t channel, bool enable) {
  if (channel < 1 || channel > maxChan) return -1;

  int board = (channel - 1) / channelsPerBoard;

#ifdef IVPULSEMUX

  digitalWrite(iv_on_pins[board], enable ? HIGH : LOW);

#else

  if (enable)
    bitSet(outState[board], senseRelayBit);
  else
    bitClear(outState[board], senseRelayBit);

#endif

  return 0;
}

void printHelp() {
  debug->println("a <channel>           : activate <channel>, clearing everything else and setting bias and sense");
  debug->println("s <channel> <state>   : set sense relay of <channel> to <state>");
  debug->println("t                     : print temperature (Kelvin) once per second until another character is received");
  debug->println("b <channel> <state>   : set bias relay of <channel> to <state>");
#ifndef IVPULSEMUX
  debug->println("q <from> <to> <delay> : activate channel from <from> to <to> in seQuence, with <delay> (mS) per step");
#endif
  debug->println("      (if <delay> < 0 wait for a trigger after each channel activation, and then wait - <delay> ");
  debug->println("d                     : dump state");
  debug->println("w                     : write state to relays");
#ifdef IVPULSEMUX
  debug->println("y                     : activate BYPASS if uppsercase, deactivate if lowercase");
#endif
  debug->println("z                     : zero state (and write to relays)");
}

// This is not tested / debugged yet
void tempRead() {

  // read internal temperature sensor
  while (control->read() == -1) {
    // Set VREF to 1.1V
    VREF.CTRLA = 0x11;  // 1V1 for ADC0, don't care for AC0
    VREF.CTRLB = 0x02;  // force enable of VREF for ADC0 (probably not needed)

    //ADC0.CTRLA = 0;       // disable until we're ready
    ADC0.CTRLC = 0x46;  // 128 prescaler, internal voltage reference, SAMPCAP = 1

    ADC0.MUXPOS = 0x1E;  // TEMPSENSE

    ADC0.CTRLD = 0xE0;     // maximum INITDLY
    ADC0.SAMPCTRL = 0x1f;  // maximum SAMPLEN

    ADC0.CTRLA = 1;  // enable ADC

    ADC0.COMMAND = 1;  // start conversion

    while (ADC0.COMMAND & 0x01)
      ;

    debug->println((ADC0.RES - SIGROW_TEMPSENSE1) * (SIGROW_TEMPSENSE0 / 256.0));
    delay(1000);
  }
}
