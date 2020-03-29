import torch
import math
import logging
import sys
import numpy as np

class NumericEncoder:

    def __init__(self, data_type=None, is_target=False):
        self._type = data_type
        self._mean = None
        self._pytorch_wrapper = torch.FloatTensor
        self._prepared = False
        self.is_target = is_target
        self.decode_log = True

    def prepare_encoder(self, priming_data):
        if self._prepared:
            raise Exception('You can only call "prepare_encoder" once for a given encoder.')

        value_type = 'int'
        for number in priming_data:
            try:
                number = float(number)
            except:
                continue

            if np.isnan(number):
                err = 'Lightwood does not support working with NaN values !'
                logging.error(err)
                raise Exception(err)

            if int(number) != number:
                value_type = 'float'

        self._type = value_type if self._type is None else self._type
        self._mean = np.sum(priming_data) / len(priming_data)
        self._prepared = True

    def encode(self, data):
        if not self._prepared:
            raise Exception('You need to call "prepare_encoder" before calling "encode" or "decode".')

        ret = []
        for real in data:
            if self.is_target:
                vector = [0] * 3
                try:
                    vector[0] = math.log(abs(real)) if abs(real) > 0 else - 20
                    vector[1] = 1 if real < 0 else 0
                    vector[2] = real/self._mean
                except Exception as e:
                    vector = [0] * 3
                    logging.error(f'Can\'t encode target value: {real}, exception: {e}')

            else:
                vector = [0] * 4
                try:
                    if real is None:
                        vector[1] = 0
                    else:
                        vector[1] = 1
                        vector[0] = math.log(abs(real)) if abs(real) > 0 else -20
                        vector[2] = 1 if real < 0 else 0
                        vector[3] = real/self._mean
                except Exception as e:
                    vector = [0] * 4
                    logging.error(f'Can\'t encode input value: {real}, exception: {e}')

            ret.append(vector)

        return self._pytorch_wrapper(ret)

    def decode(self, encoded_values, decode_log=None):
        if not self._prepared:
            raise Exception('You need to call "prepare_encoder" before calling "encode" or "decode".')

        if decode_log is None:
            decode_log = self.decode_log

        ret = []
        for vector in encoded_values.tolist():
            if self.is_target:
                if np.isnan(vector[0]) or vector[0] == float('inf') or np.isnan(vector[1]) or vector[1] == float('inf') or np.isnan(vector[2]) or vector[2] == float('inf'):
                    logging.error(f'Got weird target value to decode: {vector}')
                    real_value = pow(10,63)
                else:
                    if decode_log:
                        sign = -1 if vector[1] > 0.5 else 1
                        real_value = math.exp(vector[0]) * sign
                    else:
                        real_value = vector[2] * self._mean
            else:
                if vector[2] < 0.5:
                    ret.append(None)
                    continue

                real_value = vector[3] * self._mean

            if self._type == 'int':
                real_value = round(real_value)

            ret.append(real_value)
        return ret

    '''
    def encode(self, data):
        if not self._prepared:
            raise Exception('You need to call "prepare_encoder" before calling "encode" or "decode".')
        ret = []

        for number in data:
            vector_len = 4
            vector = [0]*vector_len

            if number is None:
                vector[3] = 0
                ret.append(vector)
                continue
            else:
                vector[3] = 1

            try:
                number = float(number)
            except:
                logging.warning('It is assuming that  "{what}" is a number but cannot cast to float'.format(what=number))
                ret.append(vector)
                continue

            if number < 0:
                vector[0] = 1

            if number == 0:
                vector[2] = 1
            else:
                vector[1] = math.log(abs(number))

            ret.append(vector)

        return self._pytorch_wrapper(ret)


    def decode(self, encoded_values):
        ret = []
        for vector in encoded_values.tolist():
            if not math.isnan(vector[0]):
                is_negative = True if abs(round(vector[0])) == 1 else False
            else:
                logging.warning(f'Occurance of `nan` value in encoded numerical value: {vector}')
                is_negative = False

            if not math.isnan(vector[1]):
                encoded_nr = vector[1]
            else:
                logging.warning(f'Occurance of `nan` value in encoded numerical value: {vector}')
                encoded_nr = 0

            if not math.isnan(vector[2]):
                is_zero = True if abs(round(vector[2])) == 1 else False
            else:
                logging.warning(f'Occurance of `nan` value in encoded numerical value: {vector}')
                is_zero = False

            if not math.isnan(vector[3]):
                is_none = True if abs(round(vector[3])) == 0 else False
            else:
                logging.warning(f'Occurance of `nan` value in encoded numerical value: {vector}')
                is_none = True

            if is_none:
                ret.append(0)
                continue

            if is_zero:
                ret.append(0)
                continue

            try:
                real_value = math.exp(encoded_nr)
                if is_negative:
                    real_value = -real_value
            except:
                if self._type == 'int':
                    real_value = pow(2,63)
                else:
                    real_value = float('inf')

            if self._type == 'int':
                real_value = round(real_value)

            ret.append(real_value)

        return ret
    '''


if __name__ == "__main__":
    data = [1,1.1,2,-8.6,None,0]

    encoder = NumericEncoder()

    encoder.prepare_encoder(data)
    encoded_vals = encoder.encode(data)

    assert(sum(encoded_vals[4]) == 0)
    assert(sum(encoded_vals[0]) == 1)
    assert(encoded_vals[1][1] > 0)
    assert(encoded_vals[2][1] > 0)
    assert(encoded_vals[3][1] > 0)
    for i in range(0,4):
        assert(encoded_vals[i][3] == 1)
    assert(encoded_vals[4][3] == 0)

    decoded_vals = encoder.decode(encoded_vals)

    for i in range(len(encoded_vals)):
        if decoded_vals[i] is None:
            assert(decoded_vals[i] == data[i])
        else:
            assert(round(decoded_vals[i],5) == round(data[i],5))
