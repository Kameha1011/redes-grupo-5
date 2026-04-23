import os
import sys
import unittest
from unittest import mock

SELECTIVE_REPEAT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "src", "lib", "common", "selective_repeat")
)
if SELECTIVE_REPEAT_DIR not in sys.path:
    sys.path.insert(0, SELECTIVE_REPEAT_DIR)

import Packet  # noqa: E402
import Receiver  # noqa: E402
import Sender  # noqa: E402


class FakeClock:
    def __init__(self, start: float):
        self.now = start

    def time(self) -> float:
        return self.now


class SenderTimerTests(unittest.TestCase):
    def test_check_timers_resends_after_timeout(self):
        clock = FakeClock(0.0)
        original_timeout = Sender.TIMEOUT_MS
        Sender.TIMEOUT_MS = 0.25
        try:
            with mock.patch.object(Sender.time, "time", clock.time):
                sender = Sender.Sender(window_size=3)
                pkt0 = Packet.Packet(0, False)
                sender.feed(pkt0)

                clock.now = 0.1
                self.assertEqual(sender.check_timers(), [])

                clock.now = 0.3
                self.assertEqual(sender.check_timers(), [pkt0])

                clock.now = 0.4
                self.assertEqual(sender.check_timers(), [])
        finally:
            Sender.TIMEOUT_MS = original_timeout

    def test_handle_ack_clears_timer_and_buffer(self):
        clock = FakeClock(0.0)
        with mock.patch.object(Sender.time, "time", clock.time):
            sender = Sender.Sender(window_size=3)
            pkt1 = Packet.Packet(1, False)
            sender.feed(pkt1)

            ack = Packet.Packet(1, True)
            sender.handle_ack(ack)

            idx = 1 % sender.window_size
            self.assertIsNone(sender.buffer[idx])
            self.assertTrue(sender.ack_tracker[idx])
            self.assertEqual(sender.timers[idx], 0)


class ReceiverTests(unittest.TestCase):
    def test_receive_dispatches_in_order(self):
        receiver = Receiver.Receiver(window_size=3)
        pkt0 = Packet.Packet(0, False)

        dispatched = receiver.receive(pkt0)

        self.assertEqual(dispatched, [pkt0])
        self.assertEqual(receiver.rcv_base, 1)


if __name__ == "__main__":
    unittest.main()
