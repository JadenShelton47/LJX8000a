import ctypes
import time
import LJXAwrap
import sys
import ctypes


deviceId = 0
ysize = 3200                          # Number of Y lines.
timeout_sec = 5                     # Timeout value for the acquiring image
use_external_batchStart = False     # 'True' if you start batch externally.
image_available = False             # Flag to conrirm the completion of image acquisition.
ysize_acquired = 0                  # Number of Y lines of acquired image.
z_val = []                          # The buffer for height image.
lumi_val = [] 
                      # The buffer for luminance image.

ethernetConfig = LJXAwrap.LJX8IF_ETHERNET_CONFIG()
ethernetConfig.abyIpAddress[0] = 10    # IP address
ethernetConfig.abyIpAddress[1] = 80
ethernetConfig.abyIpAddress[2] = 3
ethernetConfig.abyIpAddress[3] = 242
ethernetConfig.wPortNo = 24691          # Port No.
HighSpeedPortNo = 24692                 # Port No. for high-speed



def OpenConnection():
    print("open")
    res = LJXAwrap.LJX8IF_EthernetOpen(deviceId, ethernetConfig)
    print("LJXAwrap.LJX8IF_EthernetOpen:", hex(res))
    if res != 0:
        print("Failed to connect contoller.")
        print("Exit the program.")
        sys.exit()


def CloseConnection():
    print("close")
    res = LJXAwrap.LJX8IF_CommunicationClose(deviceId)
    print("LJXAwrap.LJX8IF_CommunicationClose:", hex(res))

def LaserOn():
    print("laserOn")
    LJXAwrap.LJX8IF_ControlLaser(deviceId,True)

def LaserOff():
    print("laserOff")
    LJXAwrap.LJX8IF_ControlLaser(deviceId,False)

def monitorData():
    #print("MonitorData")
    xpointNum = 3200            # Number of X points per one profile.
    withLumi = 1                # 1: luminance data exists, 0: not exists.

    # Specifies the position, etc. of the profiles to get.
    req = LJXAwrap.LJX8IF_GET_PROFILE_REQUEST()
    req.byTargetBank = 0x0      # 0: active bank
    req.byPositionMode = 0x0    # 0: from current position
    req.dwGetProfileNo = 0x0    # use when position mode is "POSITION_SPEC"
    req.byGetProfileCount = 10000   # the number of profiles to read.
    req.byErase = 0             # 0: Do not erase

    rsp = LJXAwrap.LJX8IF_GET_PROFILE_RESPONSE()

    profinfo = LJXAwrap.LJX8IF_PROFILE_INFO()

    # Calculate the buffer size to store the received profile data.
    dataSize = ctypes.sizeof(LJXAwrap.LJX8IF_PROFILE_HEADER)
    dataSize += ctypes.sizeof(LJXAwrap.LJX8IF_PROFILE_FOOTER)
    dataSize += ctypes.sizeof(ctypes.c_uint) * xpointNum * (1 + withLumi)
    dataSize *= req.byGetProfileCount

    dataNumIn4byte = int(dataSize / ctypes.sizeof(ctypes.c_uint))
    profdata = (ctypes.c_int * dataNumIn4byte)()

    # Send command.
    for i in range(100):
        res = LJXAwrap.LJX8IF_GetProfile(deviceId,
                                    req,
                                    rsp,
                                    profinfo,
                                    profdata,
                                    dataSize)
        trigger = profdata[1600]
        print(trigger)
        if trigger >= 0:
            print("HERE")
            LJXAwrap.LJX8IF_StartMeasure(deviceId)
            AcquireImage()   

def AcquireImage():

    global image_available
    global ysize_acquired
    global z_val
    global lumi_val

    ##################################################################
    # CHANGE THIS BLOCK TO MATCH YOUR SENSOR SETTINGS (FROM HERE)
    ##################################################################

    deviceId = 0                        # Set "0" if you use only 1 head.
    ysize = 1000                        # Number of Y lines.
    timeout_sec = 5                     # Timeout value for the acquiring image
    use_external_batchStart = False     # 'True' if you start batch externally.

    ethernetConfig = LJXAwrap.LJX8IF_ETHERNET_CONFIG()
    ethernetConfig.abyIpAddress[0] = 10   # IP address
    ethernetConfig.abyIpAddress[1] = 80
    ethernetConfig.abyIpAddress[2] = 3
    ethernetConfig.abyIpAddress[3] = 242
    ethernetConfig.wPortNo = 24691          # Port No.
    HighSpeedPortNo = 24692                 # Port No. for high-speed

    ##################################################################
    # CHANGE THIS BLOCK TO MATCH YOUR SENSOR SETTINGS (TO HERE)
    ##################################################################

    # Ethernet open
    res = LJXAwrap.LJX8IF_EthernetOpen(0, ethernetConfig)
    print("LJXAwrap.LJX8IF_EthernetOpen:", hex(res))
    if res != 0:
        print("Failed to connect contoller.")
        print("Exit the program.")
        sys.exit()

    # Initialize Hi-Speed Communication
    my_callback_s_a = LJXAwrap.LJX8IF_CALLBACK_SIMPLE_ARRAY(callback_s_a)

    res = LJXAwrap.LJX8IF_InitializeHighSpeedDataCommunicationSimpleArray(
        deviceId,
        ethernetConfig,
        HighSpeedPortNo,
        my_callback_s_a,
        ysize,
        0)
    print("LJXAwrap.LJX8IF_InitializeHighSpeedDataCommunicationSimpleArray:",
          hex(res))
    if res != 0:
        print("\nExit the program.")
        sys.exit()

    # PreStart Hi-Speed Communication
    req = LJXAwrap.LJX8IF_HIGH_SPEED_PRE_START_REQ()
    req.bySendPosition = 2
    profinfo = LJXAwrap.LJX8IF_PROFILE_INFO()

    res = LJXAwrap.LJX8IF_PreStartHighSpeedDataCommunication(
        deviceId,
        req,
        profinfo)
    print("LJXAwrap.LJX8IF_PreStartHighSpeedDataCommunication:", hex(res))
    if res != 0:
        print("\nExit the program.")
        sys.exit()

    # allocate the memory
    xsize = profinfo.wProfileDataCount
    z_val = [0] * xsize * ysize
    lumi_val = [0] * xsize * ysize

    # Start Hi-Speed Communication
    image_available = False
    res = LJXAwrap.LJX8IF_StartHighSpeedDataCommunication(deviceId)
    print("LJXAwrap.LJX8IF_StartHighSpeedDataCommunication:", hex(res))
    if res != 0:
        print("\nExit the program.")
        sys.exit()

    # Start Measure (Start Batch)
    if use_external_batchStart is False:
        LJXAwrap.LJX8IF_StartMeasure(deviceId)

    # wait for the image acquisition complete
    start_time = time.time()
    while True:
        if image_available:
            break
        if time.time() - start_time > timeout_sec:
            break
    # Stop
    res = LJXAwrap.LJX8IF_StopHighSpeedDataCommunication(deviceId)
    print("LJXAwrap.LJX8IF_StoptHighSpeedDataCommunication:", hex(res))

    # Finalize
    res = LJXAwrap.LJX8IF_FinalizeHighSpeedDataCommunication(deviceId)
    print("LJXAwrap.LJX8IF_FinalizeHighSpeedDataCommunication:", hex(res))
    monitorData()

def callback_s_a(p_header,
                 p_height,
                 p_lumi,
                 luminance_enable,
                 xpointnum,
                 profnum,
                 notify, user):

    global ysize_acquired
    global image_available
    global z_val
    global lumi_val
    print("incallbacks")
    if (notify == 0) or (notify == 0x10000):
        if profnum != 0:
            if image_available is False:
                for i in range(xpointnum * profnum):
                    z_val[i] = p_height[i]
                    if luminance_enable == 1:
                        lumi_val[i] = p_lumi[i]
                print(z_val)
                ysize_acquired = profnum
                image_available = True
    return
    

OpenConnection()
LaserOn()
monitorData()
LaserOff()
CloseConnection()
