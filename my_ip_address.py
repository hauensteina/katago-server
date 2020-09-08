import os, time

while(1):
    tt = os.popen( 'curl "https://katagui.herokuapp.com/server_ip?pwd=3515862"')
    tt.read()
    tt.close()
    time.sleep( 60)

