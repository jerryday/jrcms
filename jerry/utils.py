__author__ = 'wangdai'

import hashlib
import base64


class Obfuscator:
    _salt = b'thisfuckupobfuscatemethod'
    _head_bytes = 16
    _mid_bytes = 8
    _tail_bytes = 8

    @staticmethod
    def bytearray_to_int(byte_arr):
        return int.from_bytes(byte_arr, byteorder='big')

    @staticmethod
    def int_to_bytearray(num):
        assert isinstance(num, int) and num >= 0
        if num == 0:
            return b'0'
        result = []
        while num > 0:
            d, m = divmod(num, 256)
            result.append(m)
            num = d
        return bytes(result[::-1])

    @classmethod
    def obfuscate(cls, uid):
        if not uid:
            return ''
        uid_bytes = cls.int_to_bytearray(uid)
        seg1 = hashlib.sha1(uid_bytes).digest()[:cls._head_bytes]

        seg2 = hashlib.sha1(seg1 + cls._salt).digest()[:cls._mid_bytes]
        seg2 = cls.int_to_bytearray(uid + cls.bytearray_to_int(seg2))

        seg3 = hashlib.sha1(seg1 + seg2).digest()[:cls._tail_bytes]
        # print('seg1: ', seg1, 'seg2: ', seg2, 'seg3: ', seg3)
        return base64.urlsafe_b64encode(seg1 + seg2 + seg3).decode()

    @classmethod
    def restore(cls, obscure_str):
        if not obscure_str:
            return -1
        seg_bytes = base64.urlsafe_b64decode(obscure_str)
        seg1 = seg_bytes[:cls._head_bytes]
        seg2 = seg_bytes[cls._head_bytes:-cls._tail_bytes]
        seg3 = seg_bytes[-cls._tail_bytes:]
        # print('seg1: ', seg1, 'seg2: ', seg2, 'seg3: ', seg3)
        if hashlib.sha1(seg1 + seg2).digest()[:cls._tail_bytes] != seg3:
            return -1
        seg1 = hashlib.sha1(seg1 + cls._salt).digest()[:cls._mid_bytes]
        return cls.bytearray_to_int(seg2) - cls.bytearray_to_int(seg1)
