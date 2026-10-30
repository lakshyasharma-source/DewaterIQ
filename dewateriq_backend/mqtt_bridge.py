"""OPTIONAL MQTT transport for synthetic telemetry, publish+subscribe only.

Never subscribes to command topics or publishes to industrial/physical equipment topics.
Requires a trusted test broker and paho-mqtt. Default localhost:1883.
"""
import argparse
import json
import os
import time
from .historian import insert_records
from .sim_runner import generate, SCENARIOS
from .schema import validate_record
TOPIC='dewateriq/sim/telemetry/v1'


def client():
    import paho.mqtt.client as mqtt
    # No control subscriptions, no physical IO.
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='diq-sim-'+str(os.getpid()))


def publish(records,host='localhost',port=1883,delay=0.01):
    c=client(); c.connect(host,port,keepalive=30); c.loop_start()
    try:
        for record in records:
            validate_record(record)
            payload=json.dumps(record,separators=(',',':'))
            result=c.publish(TOPIC,payload,qos=1,retain=False)
            result.wait_for_publish(timeout=10)
            if not result.is_published(): raise RuntimeError('MQTT publish failed')
            time.sleep(delay)
    finally: c.loop_stop(); c.disconnect()


def listen(host='localhost',port=1883,path=None,max_messages=0):
    import paho.mqtt.client as mqtt
    c=client(); received=[0]
    def on_connect(client,userdata,flags,reason_code,properties):
        if reason_code!=0: raise RuntimeError('Broker connection rejected')
        client.subscribe(TOPIC,qos=1)
    def on_message(client,userdata,msg):
        try:
            item=validate_record(json.loads(msg.payload.decode('utf-8')))
            insert_records([item],path)
            received[0]+=1
            print(f"Stored {item['run_id']} t={item['timestamp_s']}",flush=True)
            if max_messages and received[0]>=max_messages: client.disconnect()
        except Exception as exc:
            print(f'Rejected synthetic telemetry: {type(exc).__name__}',flush=True)
    c.on_connect=on_connect; c.on_message=on_message
    c.connect(host,port,keepalive=30)
    c.loop_forever()
    return received[0]


def main():
    parser=argparse.ArgumentParser(description='Synthetic-only MQTT publishing/ingestion')
    parser.add_argument('direction',choices=['publish','listen'])
    parser.add_argument('--host',default=os.getenv('MQTT_HOST','localhost'))
    parser.add_argument('--port',type=int,default=int(os.getenv('MQTT_PORT','1883')))
    parser.add_argument('--scenario',choices=SCENARIOS,default='load')
    parser.add_argument('--samples',type=int,default=80)
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--count',type=int,default=0)
    opts=parser.parse_args()
    if opts.direction=='publish':
        publish(generate(opts.scenario,opts.samples,opts.seed),opts.host,opts.port)
    else: listen(opts.host,opts.port,max_messages=opts.count)

if __name__=='__main__': main()
