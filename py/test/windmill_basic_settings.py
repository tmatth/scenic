# Generated by the windmill services transformer
from windmill.authoring import WindmillTestClient
import time
import os

def test_recordingSuite2():
    client = WindmillTestClient(__name__)

    client.click(id='adb_add')
    client.type(text='bloup', id='adb_name')
    client.type(text='10.10.10.72', id='adb_address')
    client.check(id='adb_auto_answer')
    client.click(id='adb_edit')
    client.click(id='adb_join')
        
    client.select(option='video_rx', id='strm_global_setts')
    client.click(value='1')
    #START
    client.click(id='strm_start')
    time.sleep(5)
    #STOP    
    client.click(id='strm_start')    
    client.select(option='video_tx', id='strm_global_setts')
    client.click(value='2')
    #START
    client.click(id='strm_start')
    time.sleep(5)
    #STOP    
    client.click(id='strm_start')    
    client.select(option='audio_rx', id='strm_global_setts')
    client.click(value='3')
    #START    
    client.click(id='strm_start')   
    time.sleep(5)
    #STOP
    client.click(id='strm_start')    
    client.select(option='audio_tx', id='strm_global_setts')
    client.click(value='4')
    #START    
    client.click(id='strm_start')   
    time.sleep(5)
    #STOP
    client.click(id='strm_start')    
    client.select(option='video_rxtx', id='strm_global_setts')
    client.click(value='5')
    #START    
    client.click(id='strm_start')
    time.sleep(5)
    #STOP
    client.click(id='strm_start')    
    client.select(option='audio_rxtx', id='strm_global_setts')
    client.click(value='6')
    #START    
    client.click(id='strm_start')
    time.sleep(5)
    #STOP
    client.click(id='strm_start')
    client.select(option='AV_rxtx', id='strm_global_setts')
    client.click(value='7')
    #START
    client.click(id='strm_start')
    time.sleep(3)
    #STOP
    client.click(id='strm_start')
