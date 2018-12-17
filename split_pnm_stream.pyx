from cpython cimport array
import array


def split_pnm_stream(const unsigned char[:] data, Py_ssize_t n):
    cdef int length = data.shape[0]

    cdef array.array x = array.array('i')
    array.resize(x, n)

    cdef int j = 0
    while j < n:
        x.data.as_ints[j] = 0
        j += 1


    cdef int i = 0
    cdef Py_ssize_t c = 0
    while i < (length - 1):
        if data[i] == 80 and data[i+1] == 53 and c < n:
            x.data.as_ints[c] = i
            c += 1
        i += 1


    return list(x)
        
