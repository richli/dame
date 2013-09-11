from __future__ import print_function, division
""" Wrapper for the C libsir.so 

All I need to wrap are some of the functions in sir_ez.h

"""

import numpy as np
import tempfile

import ctypes
from ctypes import c_float, c_int, c_char, c_short, c_char_p, c_void_p, Structure, byref, pointer, POINTER
c_float_p = POINTER(c_float)

clib = ctypes.cdll.LoadLibrary("libc.so.6")
sirlib = ctypes.cdll.LoadLibrary("libsir.so.1")


# Constants from sir_ez.h
MAXI = 128
MAXDES = 512

# Structures
class FILE(Structure):
    # stdio FILE 
    pass

class sir_head(Structure):
    _fields_ = [
            ("nhead", c_int), 
            ("nhtype", c_int),
            ("nsx", c_int),
            ("nsy", c_int),
            ("iopt", c_int),
            ("xdeg", c_float),
            ("ydeg", c_float),
            ("ascale", c_float),
            ("bscale", c_float),
            ("a0", c_float),
            ("b0", c_float),
            ("ixdeg_off", c_int),
            ("iydeg_off", c_int),
            ("ideg_sc", c_int),
            ("iscale_sc", c_int),
            ("ia0_off", c_int),
            ("ib0_off", c_int),
            ("i0_sc", c_int),
            ("idatatype", c_int),
            ("ioff", c_int),
            ("iscale", c_int),
            ("anodata", c_float),
            ("v_min", c_float),
            ("v_max", c_float),
            ("iyear", c_int),
            ("isday", c_int),
            ("ismin", c_int),
            ("ieday", c_int),
            ("iemin", c_int),
            ("iregion", c_int),
            ("itype", c_int),
            ("ipol", c_int),
            ("ifreqhm", c_int),
            ("ispare1", c_int),
            ("title", c_char * 101),
            ("sensor", c_char * 41),
            ("type", c_char * 139),
            ("tag", c_char * 101),
            ("crproc", c_char * 101),
            ("crtime", c_char * 29),
            ("ndes", c_int),
            ("ldes", c_int),
            ("descrip", c_char_p),
            ("nia", c_int),
            ("iaopt", POINTER(c_short)),
            ("maxdes", c_int),
            ("maxi", c_int),
            ("descrip_flag", c_int),
            ("iaopt_flag", c_int),
            ("descrip_string", c_char * (MAXDES+1)),
            ("iaopt_array", c_short * MAXI),
            ]

# Function prototypes for libsir
sirlib.sir_init_head.argtypes = [POINTER(sir_head)]
sirlib.sir_init_head.restype = None
sirlib.get_sir.argtypes = [c_char_p, POINTER(sir_head), POINTER(c_float_p)]
sirlib.get_sir.restype = c_int
sirlib.sir_pix2latlon.argtypes = [c_float, c_float, c_float_p, c_float_p, POINTER(sir_head)]
sirlib.sir_pix2latlon.restype = None

# Function prototypes for libc
clib.fdopen.argtypes = [c_int, c_char_p]
clib.fdopen.restype = POINTER(FILE)
clib.free.argtypes = [c_void_p]
clib.free.restype = None

def sir_init_head(sir_head):
    sirlib.sir_init_head(sir_head)
    return

def get_sir(fname):
    """ Load all SIR data from the file

    fname: the filename to open

    returns the tuple (head, data)
    data: SIR data returned
    head: SIR header returned

    """
    # Create a new header for get_sir() to write into
    head = sir_head()       # C: sir_head head;
    data = c_float_p()      # C: float *data;

    retval = sirlib.get_sir(fname, byref(head), byref(data))
    if retval < 0:
        raise Exception("ERROR in get_sir()")

    # Copy data into a new Numpy array
    data_arr_tmp = np.copy(np.ctypeslib.as_array(data, shape=(head.nsy, head.nsx)))

    # The SIR data is upside-down and backwards, so compensate
    data_arr = np.flipud(data_arr_tmp)

    # free() the data malloc-ed from get_sir()
    clib.free(data)

    return (head, data_arr)

def pix2latlon(x, y, sir_head):
    """ Convert pixel coord to lat/lon

    x, y: x/y coord (1-based indexing)
    sir_head: the SIR header

    returns (lon, lat)

    """
    lon = c_float()
    lat = c_float()
    # Note that the y coord is flipped since the SIR indexing is upside down
    # from the image indexing
    #sirlib.sir_pix2latlon(x, sir_head.nsy - y - 1, byref(lon), byref(lat), byref(sir_head))
    # Compensated for already? TODO: Test
    # NB: sir_pix2latlon() uses 1-based indexing, so [1..nsx, 1..nsy] inclusive
    sirlib.sir_pix2latlon(x, y, byref(lon), byref(lat), byref(sir_head))
    return (lon.value, lat.value)

def print_sir_head(head):
    """ Prints the SIR header 

    Returns a string with the SIR header pretty-printed

    """
    # print_sir_head() function expects a FILE* arg, so I need to convert things
    # using a file descriptor

    # Create a temp file that will be written by print_sir_head()
    fname = tempfile.TemporaryFile()
    fd = fname.fileno()
    f_file = clib.fdopen(fd, "w")

    sirlib.print_sir_head(f_file, byref(head))

    # Now read the file contents
    fname.seek(0)
    head_string = fname.read()

    # The temp file is deleted and its file descriptor is closed during garbage
    # collection
    return head_string

def main():
    """ This function is just for testing """
    fname = "/home/earl/Downloads/mers_temp/msfa-a-Ama11-299-308.sir"
    #head = sir_head()
    #sir_init_head(head)

    head, data = get_sir(fname)
    print(head.nsx, head.nsy)

    lon, lat = pix2latlon(1, 10, head)
    print(lon, lat)

    head_string = print_sir_head(head)
    print(head_string)

if __name__ == "__main__":
    main()

