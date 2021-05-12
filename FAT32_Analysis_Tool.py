import sys, os, struct, binascii

def parse_VBR(VBR_data):
    if(validBR(VBR_data) == True): # VALID CHECK
        #print("[VBR Read Succeed!]")
        result = [] 
        result.append((VBR_data[3:11]).decode("utf-8"))
        result.append(convert_word(VBR_data[11:13]))
        result.append(VBR_data[13])
        result.append(convert_word(VBR_data[14:16]))
        result.append(VBR_data[16])
        result.append(convert_word(VBR_data[32:36]))
        result.append(convert_word(VBR_data[36:40]))
        result.append(format((struct.unpack('<I', VBR_data[0x43:0x47])[0]), 'X'))
        result.append(VBR_data[71:82].decode("utf-8"))
        return result
    else:
        print("VBR Read Failed")
        exit(1)        

def parse_FSINFO(FSINFO_data):
    if(validFSINFO(FSINFO_data) == True): # VALID CHECK
        result = []
        result.append(convert_dword(FSINFO_data[0x1e8:0x1ec]))
        result.append(convert_dword(FSINFO_data[0x1ec:0x1f0]))
        return result
    else:
        print("FSINFO Read Failed")
        exit(1)        

def parse_MBR(MBR_data): #  MBR 파싱 함수
    if(validBR(MBR_data) == True): # VALID CHECK
        #print("[MBR Read Succeed!]")
        # Partition Table
        MBR_table = []
        return_data = []

        for i in range(0, len(MBR_data[0x1BE:0x1FE]), 0x10):
            if(MBR_data[0x1BE:0x1FE][i:i+16] != b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'):
                MBR_table.append(MBR_data[0x1BE:0x1FE][i:i+16]) # MBR 테이블 넣기
            else:
                pass
            
        for i in range(len(MBR_table)): 
            result = [] # 파티션 1개
            result.append(hex(MBR_table[i][0])) # 0x80: 부팅o, 0x00: 부팅x
            result.append(hex(MBR_table[i][4])) # 0x0b: fat32 CHS, 0x0c: fat32 lba
            result.append(convert_dword(MBR_table[i][8:12])) # starting sector
            result.append(convert_dword(MBR_table[i][12:16])) # size
            return_data.append(result)
        return return_data # [[파티션1], [파티션2], ,,,]
            
    else:
        print("MBR Read Failed")
        exit(1)

def validBR(data):   # MBR or VBR
    if(hex(data[-2]) == '0x55' and hex(data[-1]) == '0xaa'):
        return 1
    else:
        return 0 

def validFSINFO(data):
    if(data[0:4].decode("utf-8") == 'RRaA' and data[484:488].decode("utf-8") == 'rrAa' and hex(data[-2]) == '0x55' and hex(data[-1]) == '0xaa'):
        return 1
    else:
        return 0

def convert_bytes(obyte):           # One Byte to int
    return struct.unpack_from("B", obyte)[0]
def convert_word(tbytes):           # Two Byte to int
    return struct.unpack_from("H", tbytes)[0]
def convert_dword(fbytes):          # Four Byte to int
    return struct.unpack_from("I", fbytes)[0]
def convert_dwordlong(ebytes):      # Eight Byte to int
    return struct.unpack_from("Q", ebytes)[0]

if __name__ == '__main__':
    
    # if len(sys.argv) != 2:
    #     print("Invalid arguments")
    #     print("usage: python {} [disk_path]".format(sys.argv[0]))
    #     sys.exit()

    # file_name = sys.argv[1]
    file_name = "sample.vhd"
    handle = open(file_name, 'rb')
    handle.seek(0)
    
    mbr = handle.read(512)
    mbr_data = parse_MBR(mbr)

    for i in range(len(mbr_data)):
        if(mbr_data[i][1] == '0xc'):
            print(
                "\n* Partition", i+1, "/", len(mbr_data), \
                "\nBoot Flag: {}".format(mbr_data[i][0]), \
                "\nPartition Type: {}".format(mbr_data[i][1]), \
                "\nPartition Starting Sector No.: {}".format(mbr_data[i][2]), \
                "\nNumber of Sectors: {} sector(s)".format(mbr_data[i][3]) 
                )
            
            # VBR
            handle.seek(mbr_data[i][2] * 512)
            vbr = handle.read(512)
            vbr_data = parse_VBR(vbr)
            print(
                "\nOEM ID: {}".format(vbr_data[0]), \
                "\nBytes Per Sector: {} byte(s)".format(vbr_data[1]), \
                "\nSectors Per Cluster: {} sector(s)".format(vbr_data[2]), \
                "\nNumber of Reserved Sector: {} sector(s)".format(vbr_data[3]), \
                "\nNumber of FATs: {}".format(vbr_data[4]), \
                "\nTotal Sectors: {} sector(s)".format(vbr_data[5]), \
                "\nSize of FATs: {}".format(vbr_data[6]), \
                "\nVolume Serial ID: {}-{}".format(vbr_data[7][0:4], vbr_data[7][4:8]), \
                "\nVolume Label: {}".format(vbr_data[8])
                )

            # FSINFO
            handle.seek((mbr_data[i][2] +1 )* 512)
            fsinfo= handle.read(512)
            fsinfo_data = parse_FSINFO(fsinfo)
            print(
                "\nNumber of Free Clusters: {} cluster(s)".format(fsinfo_data[0]), \
                "\nNext free cluster: {}".format(fsinfo_data[1])
            )

        elif(mbr_data[i][1] == '0xb'):
            print("* Partition {} has CHS FAT32 Type. Not Supported.".format(i+1))

        else:   
            print("* Partition {} is Not a FAT32 System".format(i+1))

