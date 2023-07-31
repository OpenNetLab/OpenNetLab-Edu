from onl.sim import Environment
from onl.netdev import Wire
from sender import SRSender
from receiver import SRReceiver

env = Environment()
sender = SRSender(env, 'hello world!', True)
receiver = SRReceiver(env, True)
wire1 = Wire(env, delay_dist=lambda: 10, loss_rate=0.1, debug=False)
wire2 = Wire(env, delay_dist=lambda: 10)
sender.out = wire1
wire1.out = receiver
receiver.out = wire2
wire2.out = sender

env.run(sender.proc)
print(receiver.message)
