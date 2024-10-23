import sys
import threading
from time import sleep
import RPi.GPIO as GPIO
from SX127x.board_config import BOARD
from SX127x.constants import MODE
from SX127x.LoRaArgumentParser import LoRaArgumentParser
import tx_beacon
import rx_cont



class LoRaSend(tx_beacon.LoRaBeacon):
    def __call__(self):
        super(LoRaSend, self).start()
    def __init__(self, verbose=False):
        super(LoRaSend, self).__init__(verbose)
        super(LoRaSend, self).set_mode(MODE.SLEEP)
        super(LoRaSend, self).set_dio_mapping([1,0,0,0,0,0])
    def start(self):
        global args
        sys.stdout.write("\r\nSender\r\n")
        sys.stdout.write("\rstart")
        self.tx_counter = 0
        BOARD.led_on()
        super(LoRaSend, self).write_payload([0x0f])
        super(LoRaSend, self).set_mode(MODE.TX)
        while True:
            sys.stdout.write("\r\nSender LOOP\r\n")
            sleep(5)

class LoRaReceive(rx_cont.LoRaRcvCont):
    def __call__(self):
        super(LoRaReceive, self).start()
    def __init__(self, verbose=False):
        super(LoRaReceive, self).__init__(verbose)
        super(LoRaReceive, self).set_mode(MODE.SLEEP)
        super(LoRaReceive, self).set_dio_mapping([0] * 6)
    def start(self):
        super(LoRaReceive, self).reset_ptr_rx()
        super(LoRaReceive, self).set_mode(MODE.RXCONT)
        while True:
            sleep(5)
            sys.stdout.write("\r\nReceiver\r\n")
            rssi_value = super(LoRaReceive, self).get_rssi_value()
            status = super(LoRaReceive, self).get_modem_status()
            sys.stdout.flush()
            sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))


       

parser = LoRaArgumentParser("A Edna LoRa beacon")

BOARD.setup()
loraReceiver = LoRaReceive(verbose=True)
args1 = parser.parse_args(loraReceiver)
loraReceiver.set_mode(MODE.STDBY)
loraReceiver.set_pa_config(pa_select=1)
print(loraReceiver)
#assert(loraReceiver.get_agc_auto_on() == 1)
#loraReceiver.start()

GPIO.cleanup()

BOARD.setup()
loraSender = LoRaSend(verbose=True)
loraSender.set_pa_config(pa_select=1)

parser.add_argument('--single', '-S', dest='single', default=False, action="store_true", help="Single transmission")
parser.add_argument('--wait', '-w', dest='wait', default=1, action="store", type=float, help="Waiting time between transmissions (default is 0s)")
args = parser.parse_args(loraSender)

# Erstellen und Starten des Sende Threads
sender_thread = threading.Thread(target=loraSender)

receiver_thread = threading.Thread(target=loraReceiver)

sys.stdout.write("\r\nStart Sender\r\n")
sender_thread.start()
sys.stdout.write("\r\nStart Receiver\r\n")
receiver_thread.start()

