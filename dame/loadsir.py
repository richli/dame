"""
Created on Sep 21, 2011

@author: Bradley
"""
import numpy as np

def loadsir(filename):
    """loadsir
    function [image head descrip iaopt]=loadsir('filename')

    load a sirf image into matlab.  Also sets global variables
    containing the image transformation information from file header

    image:      image array
    head:       scaled header information block
    descrip:    second header description string
    iaopt:      second header integer array
    filename:   name of sir input file
    """
    
    fid = file(filename)
    data_types = np.dtype('int16').newbyteorder('>')
    data_typec = np.dtype('int8').newbyteorder('>')
    data_typef = np.dtype('float32').newbyteorder('>')
    head = np.double(np.fromfile(fid,dtype=data_types,count=256,sep=""))  # read header
    # head = np.double(head)
    
    nhtype = head[4]
    if nhtype < 20:
        nhtype = 1.0
        head[4] = 1.0

    nhead = head[40]
    if nhtype == 1:
        nhead = 1.0
        head[40] = 1.0
        head[41] = 0.0
        head[42] = 0.0
        head[43] = 0.0

    ndes      = head[41].astype(int)
    ldes      = head[42].astype(int)
    nia       = head[43]
    idatatype = head[47]
    iopt      = head[16]    # transformation option

    if nhtype < 30:  # old header format
    # set version 3.0 parameters to header version 2.0 defaults     
        if iopt==-1:  # image only
            ideg_sc = 10.0
            iscale_sc = 1000.0
            i0_sc = 100.0
            ixdeg_off = 0.0
            iydeg_off = 0.0
            ia0_off = 0.0
            ib0_off = 0.0
        elif iopt==0: # rectalinear lat/lon
            ideg_sc = 100.0
            iscale_sc = 1000.0
            i0_sc = 100.0
            ixdeg_off = -100.0
            iydeg_off = 0.0
            ia0_off = 0.0
            ib0_off = 0.0
        elif (iopt==1) or (iopt==2): # lambert
            ideg_sc = 100.0
            iscale_sc = 1000.0
            i0_sc = 1.0
            ixdeg_off = 0.0
            iydeg_off = 0.0
            ia0_off = 0.0
            ib0_off = 0.0
        elif iopt==5: # polar stereographic
            ideg_sc = 100.0
            iscale_sc = 100.0
            i0_sc = 1.0
            ixdeg_off = -100.0
            iydeg_off = 0.0
            ia0_off = 0.0
            ib0_off = 0.0
        elif (iopt==11) or (iopt==12) or (iopt==13): # EASE grid
            ideg_sc = 10.0
            iscale_sc = 1000.0
            i0_sc = 10.0
            ixdeg_off = 0.0
            iydeg_off = 0.0
            ia0_off = 0.0
            ib0_off = 0.0
        else: #  unknown default scaling
            ideg_sc = 100.0
            iscale_sc = 1000.0
            i0_sc = 100.0
            ixdeg_off = 0.0
            iydeg_off = 0.0
            ia0_off = 0.0
            ib0_off = 0.0

        head[ 39] = iscale_sc
        head[126] = ixdeg_off
        head[127] = iydeg_off
        head[168] = ideg_sc
        head[189] = ia0_off
        head[240] = ib0_off
        head[255] = i0_sc 
    else:  # get projection parameters offset and scale factors
        iscale_sc = head[ 39]
        ixdeg_off = head[126]
        iydeg_off = head[127]
        ideg_sc   = head[168]
        ia0_off   = head[189]
        ib0_off   = head[240]
        i0_sc     = head[255]

    #    decode projection transformation 
    xdeg   = head[2]/ideg_sc - ixdeg_off
    ydeg   = head[3]/ideg_sc - iydeg_off
    ascale = head[5]/iscale_sc
    bscale = head[6]/iscale_sc
    a0     = head[7]/i0_sc - ia0_off
    b0     = head[8]/i0_sc - ib0_off
    #    get special cases which depend on transformation option
    if iopt==-1:   # image only
        pass
    elif iopt==0:  # rectalinear lat/lon
        pass
    elif (iopt==1) or (iopt==2): # lambert
        ascale = iscale_sc/head[5]
        bscale = iscale_sc/head[6]
    elif iopt==5: # polar stereographic
        pass
    elif (iopt==11) or (iopt==12) or (iopt==13): # EASE grid
        ascale = 2.0*(head[5]/iscale_sc)*6371.228/25.067525
        bscale = 2.0*(head[6]/iscale_sc)*25.067525
    else: # unknown default scaling
        print '*** Unrecognized SIR option in loadsir ***'

    head[2] = xdeg
    head[3] = ydeg
    head[5] = ascale
    head[6] = bscale
    head[7] = a0
    head[8] = b0

    if head[10]==0:  # iscale
        head[10] = 1.0
        
    s = 1.0/head[10]
    soff = 32767.0/head[10]
    if idatatype==1:
        soff = 128.0/head[10]

    ioff = head[9]
    anodata = head[48]*s + ioff + soff
    vmin = head[49]*s + ioff + soff
    vmax = head[50]*s + ioff + soff

    if idatatype==4:
        fid.close()
        fid = file(filename)
        np.fromfile(fid,dtype=data_types,count=51,sep="")
        fl = np.double(np.fromfile(fid,dtype=data_typef,count=3,sep=""))
        fid.close()
        fid = file(filename)
        np.fromfile(fid,dtype=data_types,count=256,sep="")
        anodata = fl[0]
        vmin = fl[1]
        vmax = fl[2]

    head[45] = head[45]*0.1
    head[48] = anodata
    head[49] = vmin
    head[50] = vmax

    descrip = []
    iaopt = []

    if nhead>1:
        if ndes>0:
            descrip = np.fromfile(fid,dtype=data_typec,count=ndes*512,sep="")
            # Convert int value to ascii char
            descrip = np.array([chr(f) for f in descrip[0:ldes+1]])
            # The bytes are swapped, so unswap them
            order = np.arange(ldes+1).reshape((-1,2))
            order = np.roll(order, 1, axis=1)
            order = order.flatten()
            descrip = descrip[order]
            # Convert char array to Python string, discard any null characters at the end
            descrip = descrip.tostring().rstrip('\0')
        if nia>0:
            nia1 = 256.0*np.ceil(nia/256)
            iaopt = np.double(np.fromfile(fid,dtype=data_types,count=nia1,sep=""))
            iaopt = np.transpose(iaopt[1:nia])

    # read image data
    if idatatype==1: 
        # disp(['Read byte data: ' num2str(head(1)) ' x ' num2str(head(2))]);
        im_in = np.double(np.fromfile(fid,dtype=data_typec,count=int(head[0]*head[1]),sep=""))  # read byte image data
        image = np.flipud(np.reshape(s*im_in+soff+ioff,(head[1],head[0]),order='C'))   # scale data to floating point and
        # change origin location 
    elif idatatype==4:
        # disp(['Read float data: ' num2str(head(1)) ' x ' num2str(head(2))]);
        im_in = np.double(np.fromfile(fid,dtype=data_typef,count=int(head[0]*head[1]),sep=""))
        image = np.flipud(np.reshape(im_in,(head[1],head[0]),order='C'))  # read floating point data
    else:
        # disp(['Read integer data: ' num2str(head(1)) ' x ' num2str(head(2))]);
        im_in = np.double(np.fromfile(fid,dtype=data_types,count=int(head[0]*head[1]),sep=""))  # read integer image data
        image = np.flipud(np.reshape(s*im_in+soff+ioff,(int(head[1]),int(head[0])),order='C'))   # scale data to floating point and
        # change origin location for display

    if nhtype==1:                     # if old-style header, set default values
        vmin = min(image.flatten(1))
        vmax = max(image.flatten(1))
        anodata = vmin
        head[48] = anodata
        head[49] = vmin
        head[50] = vmax
        if vmin==-32:
            head[18] = 1.0
        elif vmin==-3.2:
            head[18] = 2.0
            
        head[44] = 2.0
        head[45] = 53.0

    fid.close()
    return image, head, descrip, iaopt
