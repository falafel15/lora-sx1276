import sys
import threading
from time import sleep
import RPi.GPIO as GPIO
from SX127x.LoRa import LoRa
from SX127x.board_config import BOARD
from SX127x.constants import MODE
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser

class LoRaBeacon(LoRa):

    tx_counter = 0
    def __call__(self):
        self.start()
    def __init__(self, verbose=False):
        super(LoRaBeacon, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([1,0,0,0,0,0])

    def on_rx_done(self):
        print("\nRxDone")
        print(self.get_irq_flags())
        print(map(hex, self.read_payload(nocheck=True)))
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        global args
        self.set_mode(MODE.STDBY)
        self.clear_irq_flags(TxDone=1)
        sys.stdout.flush()
        self.tx_counter += 1
        sys.stdout.write("\rtx #%d" % self.tx_counter)
        if args.single:
            print
            sys.exit(0)
        BOARD.led_off()
        sleep(args.wait)
        self.write_payload([0x0f])
        BOARD.led_on()
        self.set_mode(MODE.TX)

    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())

    def start(self):
        global args
        sys.stdout.write("\r\nSender\r\n")
        sys.stdout.write("\rstart")
        self.tx_counter = 0
        BOARD.led_on()
        self.write_payload([0x0f])
        self.set_mode(MODE.TX)
        while True:
            sys.stdout.write("\r\nSender LOOP\r\n")
            sleep(5)

class LoRaRcvCont(LoRa):
    def __call__(self):
        self.start()
    def __init__(self, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

    def on_rx_done(self):
        BOARD.led_on()
        print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        print(bytes(payload).decode())
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        BOARD.led_off()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        print("\nTxDone")
        print(self.get_irq_flags())

    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())

    def start(self):
       
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(5)
            sys.stdout.write("\r\nReceiver\r\n")
            rssi_value = self.get_rssi_value()
            status = self.get_modem_status()
            sys.stdout.flush()
            sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))

    
# GPIO-Warnungen deaktivieren und GPIOs bereinigen
#GPIO.setwarnings(False)
#GPIO.cleanup()

# Setup des Boards (Initialisierung der GPIOs)
#BOARD.setup()

parser = LoRaArgumentParser("A Edna LoRa beacon")

BOARD.setup()
loraReceiver = LoRaRcvCont(verbose=True)
args1 = parser.parse_args(loraReceiver)
loraReceiver.set_mode(MODE.STDBY)
loraReceiver.set_pa_config(pa_select=1)
print(loraReceiver)
#assert(loraReceiver.get_agc_auto_on() == 1)
#loraReceiver.start()

GPIO.cleanup()
GPIO.setwarnings(False)
BOARD.setup()
loraSender = LoRaBeacon(verbose=True)
loraSender.set_pa_config(pa_select=1)

parser.add_argument('--single', '-S', dest='single', default=False, action="store_true", help="Single transmission")
parser.add_argument('--wait', '-w', dest='wait', default=1, action="store", type=float, help="Waiting time between transmissions (default is 0s)")
args = parser.parse_args(loraSender)
#loraSender.start()
# Erstellen und Starten des Sende Threads
sender_thread = threading.Thread(target=loraSender)

receiver_thread = threading.Thread(target=loraReceiver)

sys.stdout.write("\r\nStart Sender\r\n")
sender_thread.start()
sys.stdout.write("\r\nStart Receiver\r\n")
receiver_thread.start()

# Warten, bis beide Threads beendet sind
#sender_thread.join()
#receiver_thread.join()
