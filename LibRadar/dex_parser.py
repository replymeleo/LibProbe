#!/usr/bin/env python
#coding:utf-8

# BSD 2-Clause License
#
# Copyright (c) [2016], [guanchao wen], shuwoom.wgc@gmail.com
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import binascii

def safe_read(f, size):
    """
    从文件对象 f 中读取 size 个字节。
    若实际读到的长度 < size，则返回 None。
    """
    data = f.read(size)
    if data is None or len(data) < size:
        return None
    return data


def byte_to_buma(val):
    binVal = bin(val)[2:].zfill(8)
    if binVal[0:1] == '0':
        return val
    sb = ''
    for i in range(7):
        if binVal[i+1:i+2] == '0':
            sb += '1'
        else:
            sb += '0'

    return -(int(sb, 2) + 1)

def word_to_buma(val):
    binVal = bin(val)[2:].zfill(16)
    if binVal[0:1] == '0':
        return val
    sb = ''
    for i in range(15):
        if binVal[i+1:i+2] == '0':
            sb += '1'
        else:
            sb += '0'

    return -(int(sb, 2) + 1)

def reverse_hex(binary_input):
    return binascii.hexlify(binascii.unhexlify(binary_input)[::-1])

"""

# Not Used?  zachary 20170105

def dword_to_buma(val):
    binVal = bin(val)[2:].zfill(32)
    if binVal[0:1] == '0':
        return val
    sb = ''
    for i in range(31):
        if binVal[i+1:i+2] == '0':
            sb += '1'
        else:
            sb += '0'

    return -(int(sb, 2) + 1)
"""
"""
############### OPCODE #################
"""
def getOpCode(opcode):
    """
    参考: dalvik-bytecode
    """
    if opcode == 0x00 : return '10x', 'nop'
    if opcode == 0x01 : return '12x', 'move vA, vB'
    if opcode == 0x02 : return '22x', 'move/from16 vAA, vBBBB'
    if opcode == 0x03 : return '32x', 'move/16 vAAAA, vBBBB'
    if opcode == 0x04 : return '12x', 'move-wide vA, vB'
    if opcode == 0x05 : return '22x', 'move-wide/from16 vAA, vBBBB'
    if opcode == 0x06 : return '32x', 'move-wide/16 vAAAA, vBBBB'
    if opcode == 0x07 : return '12x', 'move-object vA, vB'
    if opcode == 0x08 : return '22x', 'move-object/from16 vAA, vBBBB'
    if opcode == 0x09 : return '32x', 'move-object/16 vAAAA, vBBBB'
    if opcode == 0xa : return '11x', 'move-result vAA'
    if opcode == 0xb : return '11x', 'move-result-wide vAA'
    if opcode == 0xc : return '11x', 'move-result-object vAA'
    if opcode == 0xd : return '11x', 'move-exception vAA'
    if opcode == 0xe : return '10x', 'return-void'
    if opcode == 0xf : return '11x', 'return vAA'
    if opcode == 0x10 : return '11x', 'return-wide'
    if opcode == 0x11 : return '11x', 'return-object vAA'
    if opcode == 0x12 : return '11n', 'const/4 vA, #+B'
    if opcode == 0x13 : return '21s', 'const/16 vAA, #+BBBB'
    if opcode == 0x14 : return '31i', 'const vAA, #+BBBBBBBB'
    if opcode == 0x15 : return '21h', 'const/high16 vAA, #+BBBB0000'
    if opcode == 0x16 : return '21s', 'const-wide/16 vAA, #+BBBB'
    if opcode == 0x17 : return '31i', 'const-wide/32 vAA, #+BBBBBBBB'
    if opcode == 0x18 : return '51l', 'const-wide vAA, #+BBBBBBBBBBBBBBBB'
    if opcode == 0x19 : return '21h', 'const-wide/high16 vAA, #+BBBB000000000000'
    if opcode == 0x1a : return '21c', 'const-string vAA, string@BBBB'
    if opcode == 0x1b : return '31c', 'const-string/jumbo vAA, string@BBBBBBBB'
    if opcode == 0x1c : return '21c', 'const-class vAA, type@BBBB'
    if opcode == 0x1d : return '11x', 'monitor-enter vAA'
    if opcode == 0x1e : return '11x', 'monitor-exit vAA'
    if opcode == 0x1f : return '21c', 'check-cast vAA, type@BBBB'
    if opcode == 0x20 : return '22c', 'instance-of vA, vB, type@CCCC'
    if opcode == 0x21 : return '12x', 'array-length vA, vB'
    if opcode == 0x22 : return '21c', 'new-instance vAA, type@BBBB'
    if opcode == 0x23 : return '22c', 'new-array vA, vB, type@CCCC'
    if opcode == 0x24 : return '35c', 'filled-new-array {vD, vE, vF, vG, vA}, type@CCCC'
    if opcode == 0x25 : return '3rc', 'filled-new-array/range {vCCCC .. vNNNN}, type@BBBB'
    if opcode == 0x26 : return '31t', 'fill-array-data vAA, +BBBBBBBB'
    if opcode == 0x27 : return '11x', 'throw vAA'
    if opcode == 0x28 : return '10t', 'goto +AA'
    if opcode == 0x29 : return '20t', 'goto/16 +AAAA'
    if opcode == 0x2a : return '30t', 'goto/32 +AAAAAAAA'
    if opcode == 0x2b : return '31t', 'packed-switch vAA, +BBBBBBBB'
    if opcode == 0x2c : return '31t', 'sparse-switch vAA, +BBBBBBBB'
    if opcode >= 0x2d and opcode <= 0x31 : return '23x', 'cmpkind vAA, vBB, vCC'
    if opcode >= 0x32 and opcode <= 0x37 : return '22t', 'if-test vA, vB, +CCCC'
    if opcode >= 0x38 and opcode <= 0x3d : return '21t', 'if-testz vAA, +BBBB'
    if opcode >= 0x3e and opcode <= 0x43 : return '10x', 'unused'
    if opcode >= 0x44 and opcode <= 0x51 : return '23x', 'arrayop vAA, vBB, vCC'
    if opcode >= 0x52 and opcode <= 0x5f : return '22c', 'iinstanceop vA, vB, field@CCCC'
    if opcode >= 0x60 and opcode <= 0x6d: return '21c', 'sstaticop vAA, field@BBBB'
    if opcode >= 0x6e and opcode <= 0x72 : return '35c', 'invoke-kind {vD, vE, vF, vG, vA}, meth@CCCC'
    if opcode == 0x73 : return '10x', 'unused'
    if opcode >= 0x74 and opcode <= 0x78 : return '3rc', 'invoke-kind/range {vCCCC .. vNNNN}, meth@BBBB'
    if opcode >= 0x79 and opcode <= 0x7a : return '10x', 'unused'
    if opcode >= 0x7b and opcode <= 0x8f : return '12x', 'unop vA, vB'
    if opcode >= 0x90 and opcode <= 0xaf : return '23x', 'binop vAA, vBB, vCC'
    if opcode >= 0xb0 and opcode <= 0xcf : return '12x', 'binop/2addr vA, vB'
    if opcode >= 0xd0 and opcode <= 0xd7 : return '22s', 'binop/lit16 vA, vB, #+CCCC'
    if opcode >= 0xd8 and opcode <= 0xe2 : return '22b', 'binop/lit8 vAA, vBB, #+CC'
    if opcode >= 0xe3 and opcode <= 0xfe : return '10x', 'unused'
    if opcode == 0x00ff : return '41c', 'const-class/jumbo vAAAA, type@BBBBBBBB'
    if opcode == 0x01ff : return '41c', 'check-cast/jumbo vAAAA, type@BBBBBBBB'
    if opcode == 0x02ff : return '52c', 'instance-of/jumbo vAAAA, vBBBB, type@CCCCCCCC'
    if opcode == 0x03ff : return '41c', 'new-instance/jumbo vAAAA, type@BBBBBBBB'
    if opcode == 0x04ff : return '52c', 'new-array/jumbo vAAAA, vBBBB, type@CCCCCCCC'
    if opcode == 0x05ff : return '52rc', 'filled-new-array/jumbo {vCCCC .. vNNNN}, type@BBBBBBBB'
    if opcode >= 0x06ff and opcode <= 0x13ff: return '52c', 'iinstanceop/jumbo vAAAA, vBBBB, field@CCCCCCCC'
    if opcode >= 0x14ff and opcode <= 0x21ff: return '41c', 'sstaticop/jumbo vAAAA, field@BBBBBBBB'
    if opcode >= 0x22ff and opcode <= 0x26ff: return '5rc', 'invoke-kind/jumbo {vCCCC .. vNNNN}, meth@BBBBBBBB'

"""
############### OPCODE END #################
"""

"""
############### InstrUtils #################
"""
class DecodedInstruction(object):
    """docstring for DecodedInstruction"""
    def __init__(self):
        super(DecodedInstruction, self).__init__()
        self.vA = None
        self.vB = None
        self.vC = None
        self.vD = None
        self.vE = None
        self.vF = None
        self.vG = None
        self.opcode = None
        self.op = None
        self.indexType = None
        self.smaliCode = None
        # DeCode.insns指令集内相对于起始地址的offset
        self.offset = None
        # 代码片段长度
        self.length = None

def dexDecodeInstruction(dexFile, dexCode, offset):
    byteCounts = int(offset / 4)
    insns = dexCode.insns

    if insns == '':
        return None

    decodedInstruction = DecodedInstruction()
    opcode = int(insns[offset:offset+2], 16)
    formatIns, syntax = getOpCode(opcode)

    decodedInstruction.opcode = opcode

    if formatIns == '10x':
        # Format: 00|op <=> op
        # (1) opcode=00 nop
        if opcode == 0x00:
            decodedInstruction.op = 'nop'
            decodedInstruction.smaliCode = 'nop'
            decodedInstruction.offset = offset
            decodedInstruction.length = 4

        # (2) opcode=0e return-void
        if opcode == 0x0e:
            decodedInstruction.op = 'return-void'
            decodedInstruction.smaliCode = 'return-void'
            decodedInstruction.offset = offset
            decodedInstruction.length = 4

        # (3) opcode=3e..43 unused
        if opcode >= 0x3e and opcode <= 0x43:
            decodedInstruction.op = 'unused'
            decodedInstruction.smaliCode = 'unused'
            decodedInstruction.offset = offset
            decodedInstruction.length = 4

        # (4) opcode=73 unused
        if opcode == 0x73:
            decodedInstruction.op = 'unused'
            decodedInstruction.smaliCode = 'unused'
            decodedInstruction.offset = offset
            decodedInstruction.length = 4

        # (5) opcode=79..7a unused
        if opcode >= 0x79 and opcode <= 0x7a:
            decodedInstruction.op = 'unused'
            decodedInstruction.smaliCode = 'unused'
            decodedInstruction.offset = offset
            decodedInstruction.length = 4

        # (6) opcode=e3..fe unused
        if opcode >= 0xe3 and opcode <= 0xfe:
            decodedInstruction.op = 'unused'
            decodedInstruction.smaliCode = 'unused'
            decodedInstruction.offset = offset
            decodedInstruction.length = 4

    elif formatIns == '12x': # op vA, vB
        # Format: B|A|op <=> op vA, vB
        op = '????'
        # (1) opcode=01 move vA, vB
        if opcode == 0x01:
            op = 'move'
        # (2) opcode=04 move-wide vA, vB
        if opcode == 0x04:
            op = 'move-wide'
        # (3) opcode=07 move-object vA, vB
        if opcode == 0x07:
            op = 'move-object'
        # (4) opcode=21 array-length vA, vB
        if opcode == 0x21:
            op = 'array-length'
        # (5) opcode7b..8f unop vA, vB
        if opcode >= 0x7b and opcode <= 0x8f:
            unop = ['neg-int', 'not-int', 'neg-long', 'not-long', 'neg-float', 'neg-double', 'int-to-long', 'int-to-float', 'int-to-double',
                    'long-to-int', 'long-to-float', 'long-to-double', 'float-to-int', 'float-to-long', 'float-to-double',
                    'double-to-int', 'double-to-long', 'double-to-float', 'int-to-byte', 'int-to-char', 'int-to-short']
            op = unop[opcode - 0x7b]
        # (6) opcode=b0..cf binop/2addr vA, vB
        if opcode >= 0xb0 and opcode <= 0xcf:
            ops = ['add-int/2addr', 'sub-int/2addr', 'mul-int/2addr', 'div-int/2addr', 'rem-int/2addr', 'and-int/2addr', 'or-int/2addr', 'xor-int/2addr', 'shl-int/2addr', 'shr-int/2addr', 'ushr-int/2addr',
                     'add-long/2addr', 'sub-long/2addr', 'mul-long/2addr', 'div-long/2addr', 'rem-long/2addr', 'and-long/2addr', 'or-long/2addr', 'xor-long/2addr', 'shl-long/2addr', 'shr-long/2addr','ushr-long/2addr',
                     'add-float/2addr', 'sub-float/2addr', 'mul-float/2addr', 'div-float/2addr', 'rem-float/2addr',
                     'add-double/2addr', 'sub-double/2addr', 'mul-double/2addr', 'div-double/2addr', 'rem-double/2addr']
            op = ops[opcode - 0xb0]

        B = int(insns[offset + 2:offset + 3], 16)
        A = int(insns[offset + 3:offset + 4], 16)

        decodedInstruction.op = op
        decodedInstruction.vA = A
        decodedInstruction.vB = B
        decodedInstruction.smaliCode = '%s v%d, v%d' % (op, A, B)
        decodedInstruction.offset = offset
        decodedInstruction.length = 4

    elif formatIns == '11n':
        # Format: B|A|op <=> # op vA, #+B
        # (1) opcode=12 const/4 vA, #+B
        B = int(insns[offset+2:offset+3], 16)
        A = int(insns[offset+3:offset+4], 16)

        decodedInstruction.op = 'const/4'
        decodedInstruction.vA = A
        decodedInstruction.B = B
        decodedInstruction.smaliCode = 'const/4 v%d, #+%d' % (A, B)
        decodedInstruction.offset = offset
        decodedInstruction.length = 4

    elif formatIns == '11x':
        # Format: AA|op <=> # op vAA
        op = '????'
        # (1) opcode=0a move-result vAA
        if opcode == 0x0a:
            op = 'move-result'
        # (2) opcode=0b move-result-wide vAA
        if opcode == 0x0b:
            op = 'move-result-wide'
        # (3) opcode=0c move-result-object vAA
        if opcode == 0x0c:
            op = 'move-result-object'
        # (4) opcode=0d move-exception vAA
        if opcode == 0x0d:
            op = 'move-exception'
        # (5) opcode=0f return vAA
        if opcode == 0x0f:
            op = 'return'
        # (6) opcode=10 return-wide vAA
        if opcode == 0x10:
            op = 'return-wide'
        # (7) opcode=11 return-object vAA
        if opcode == 0x11:
            op = 'return-object'
        # (8) opcode=1d monitor-enter vAA
        if opcode == 0x1d:
            op = 'monitor-enter'
        # (9) opcode=1e monitor-exit vAA
        if opcode == 0x1e:
            op = 'monitor-exit'
        # (10) opcode=27 throw vAA
        if opcode == 0x27:
            op = 'throw'

        AA = int(insns[offset + 2:offset + 4], 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.smaliCode = '%s v%d' % (op, AA)
        decodedInstruction.offset = offset
        decodedInstruction.length = 4

    elif formatIns == '10t':
        # Format: AA|op <=> # op +AA
        # (1) opcode=28 goto +AA
        AA = int(insns[offset + 2:offset + 4], 16)
        buma = byte_to_buma(AA)

        decodedInstruction.op = 'goto'
        decodedInstruction.vA = AA
        decodedInstruction.smaliCode = 'goto %s //%s' % (hex(int(offset/4)+buma), hex(buma))
        decodedInstruction.offset = offset
        decodedInstruction.length = 4

    elif formatIns == '20t':
        # Format: 00|op AAAA <=> # op +vAAAA
        # (1) opcode=29 goto/16 +AAAA
        if opcode == 0x29:
            AAAA = int(insns[offset + 2:offset + 8], 16)
            buma = word_to_buma(int(reverse_hex(insns[offset + 4:offset + 8]), 16))

            decodedInstruction.op = 'goto/16'
            decodedInstruction.vA = AAAA
            decodedInstruction.smaliCode = 'goto/16 %s //%s' % (hex(int(offset/4)+buma), hex(buma))
            decodedInstruction.offset = offset
            decodedInstruction.length = 8

    elif formatIns == '20bc':
        # Format: AA|op BBBB <=> op AA, kind@BBBB
        # 无opcode
        pass
    elif formatIns == '22x':
        # Format: AA|op BBBB <=> op vAA, vBBBB
        op = '????'
        # (1) opcode=02 move/from16 vAA, vBBBB
        if opcode == 0x02:
            op = 'move/from16'
        # (2) opcode=05 move-wide/from16 vAA, vBBBB
        if opcode == 0x05:
            op = 'move-wide/from16'
        # (3) opcode=08 move-object/from16 vAA, vBBBB
        if opcode == 0x08:
            op = 'move-object/from16'

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBB = int(reverse_hex(insns[offset + 4:offset + 8]), 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = BBBB
        decodedInstruction.smaliCode = '%s v%d, v%s' % (op, AA, BBBB)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '21t':
        # Format: AA|op BBBB <=> op vAA, +BBBB
        op = '????'
        # (1) opcode=38..3d if-testz vAA, +BBBB
        if opcode >= 0x38 and opcode <= 0x3d:
            ops = ['if-eqz', 'if-nez', 'if-ltz', 'if-gez', 'if-gtz', 'if-lez']
            op = ops[opcode - 0x38]

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBB = int(reverse_hex(insns[offset + 4:offset + 8]), 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = BBBB
        decodedInstruction.smaliCode = '%s v%d, %s //+%s' % (op, AA, hex(BBBB+int(offset/4)), hex(BBBB))
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '21s':
        # Format: AA|op BBBB <=> op vAA, #+BBBB
        op = '????'
        # (1) opcode=13 const/16 vAA, #_BBBB
        if opcode == 0x13:
            op = 'const/16'
        # (2) opcode=16 const-wide/16 vAA, #+BBBB
        if opcode == 0x16:
            op = 'const-wide/16'

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBB = int(reverse_hex(insns[offset + 4:offset + 8]), 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = BBBB
        decodedInstruction.smaliCode = '%s v%d, #+%s' % (op, AA, BBBB)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '21h':
        # Format: AA|op BBBB <=> op vAA, #+BBBB0000[00000000]
        AA = int(insns[offset + 2:offset + 4], 16)
        BBBB = reverse_hex(insns[offset + 4:offset + 8]).decode()

        # (1) opcode=15 const/high16 vAA, #+BBBB0000
        if opcode == 0x15:
            op = 'const/high16'

            decodedInstruction.op = op
            decodedInstruction.vA = AA
            decodedInstruction.vB = int(BBBB + '0000', 16)
            decodedInstruction.smaliCode = '%s v%d, #+%s' % (op, AA, int(BBBB + '0000', 16))
            decodedInstruction.offset = offset
            decodedInstruction.length = 8

        # (2) opcode=19 const-wide/high16 vAA, #+BBBB000000000000
        if opcode == 0x19:
            op = 'const-wide/high16'

            decodedInstruction.op = op
            decodedInstruction.vA = AA
            decodedInstruction.vB = int(BBBB + '000000000000', 16)
            decodedInstruction.smaliCode = '%s v%d, #+%s' % (op, AA, int(BBBB + '000000000000', 16))
            decodedInstruction.offset = offset
            decodedInstruction.length = 8

    elif formatIns == '21c':
        # Format: AA|op BBBB <=> op vAA, [type|field|string]@BBBB
        indexType = '????'
        op = '????'
        indexStr = ''

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBB = reverse_hex(insns[offset + 4:offset + 8])

        # (1) opcode=1a const-string vAA, string@BBBB
        if opcode == 0x1a:
            op = 'const-string'
            indexType = 'string'
            indexStr = dexFile.getDexStringId(int(BBBB, 16))
        # (2) opcode=1c const-class vAA, type@BBBB
        if opcode == 0x1c:
            op = 'const-class'
            indexType = 'type'
            indexStr = dexFile.getDexTypeId(int(BBBB, 16))
        # (3) opcode=1f check-cast vAA, type@BBBB
        if opcode == 0x1f:
            op = 'check-cast'
            indexType = 'type'
            indexStr = dexFile.getDexTypeId(int(BBBB, 16))
        # (4) opcode=22 new-instance vAA, type@BBBB
        if opcode == 0x22:
            op = 'new-instance'
            indexType = 'type'
            indexStr = dexFile.getDexTypeId(int(BBBB, 16))
        # (5) opcode=60..6d sstaticop vAA, field@BBBB
        if opcode >= 0x60 and opcode <=0x6d:
            sstaticop = ['sget', 'sget-wide', 'sget-object', 'sget-boolean', 'sget-byte', 'sget-char',
                         'sget-char', 'sget-short', 'sput', 'sput-wide', 'sput-object', 'sput-boolean',
                         'sput-byte', 'sput-char', 'sput-short']
            op = sstaticop[opcode - 0x60]
            indexType = 'field'
            dexFieldIdObj = dexFile.DexFieldIdList[int(BBBB, 16)]
            indexStr = dexFieldIdObj.toString(dexFile)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = int(BBBB, 16)
        decodedInstruction.indexType = indexType
        decodedInstruction.smaliCode = '%s v%d, %s@%s //%s' % (op, AA, indexType, BBBB, indexStr)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '23x':
        # Format: AA|op CC|BB <=> op vAA, vBB, vCC
        op = '????'
        # (1) opcode=2d..31 cmpkind vAA, vBB, vCC
        if opcode >= 0x2d and opcode <= 0x31:
            cmpkind = ['cmpl-float', 'cmpg-float', 'cmpl-double', 'cmpg-double', 'cmp-long']
            op =cmpkind[opcode - 0x2d]
        # (2) opcode=44..51 arrayop vAA, vBB, vCC
        if opcode >= 0x44 and opcode <= 0x51:
            arrayop = ['aget', 'aget-wide', 'aget-object', 'aget-boolean', 'aget-byte', 'aget-char', 'aget-short',
                       'aput', 'aput-wide', 'aput-object', 'aput-boolean', 'aput-byte', 'aput-char', 'aput-short']
            op = arrayop[opcode - 0x44]
        # (3) opcode=90..af binop vAA, vBB, vCC
        if opcode >= 0x90 and opcode <= 0xaf:
            binop = ['add-int', 'sub-int', 'mul-int', 'div-int', 'rem-int', 'and-int', 'or-int', 'xor-int', 'shl-int', 'shr-int', 'ushr-int',
                     'add-long', 'sub-long', 'mul-long', 'div-long', 'rem-long', 'and-long', 'or-long', 'xor-long', 'shl-long', 'shr-long', 'ushr-long',
                     'add-float', 'sub-float', 'mul-float', 'div-float', 'rem-float',
                     'add-double', 'sub-double', 'mul-double', 'div-double', 'rem-double']
            op = binop[opcode - 0x90]

        AA = int(insns[offset + 2:offset + 4], 16)
        BB = int(insns[offset + 4:offset + 6], 16)
        CC = int(insns[offset + 6:offset + 8], 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = BB
        decodedInstruction.vC = CC
        decodedInstruction.smaliCode = '%s v%d, v%d, v%d' % (op, AA, BB, CC)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '22b':
        # Format: AA|op CC|BB <=> op vAA, vBB, #+CC
        # (1) opcode=d8..e2 binop/lit8 vAA, vBB, #+CC
        if opcode >= 0xd8 and opcode <= 0xe2:
            ops = ['add-int/lit8', 'rsub-int/lit8', 'mul-int/lit8', 'div-int/lit8', 'rem-int/lit8', 'and-int/lit8',
                   'or-int/lit8', 'xor-int/lit8', 'shl-int/lit8', 'shr-int/lit8', 'ushr-int/lit8']
            op = ops[opcode - 0xd8]

        AA = int(insns[offset + 2:offset + 4], 16)
        BB = int(insns[offset + 4:offset + 6], 16)
        CC = int(insns[offset + 6:offset + 8], 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = BB
        decodedInstruction.vC = CC
        decodedInstruction.smaliCode = '%s v%d, v%d, #+v%d' % (op, AA, BB, CC)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '22t':
        # Format: B|A|op CCCC <=> op vA, vB, +CCCC
        op = '????'
        # (1) opcode=32..37 if-test vA, vB, +CCCC
        if opcode >=0x32 and opcode <= 0x37:
            ops = ['if-eq', 'if-ne', 'if-lt', 'if-ge', 'if-gt', 'if-le']
            op = ops[opcode - 0x32]
        B = int(insns[offset + 2: offset + 3], 16)
        A = int(insns[offset + 3: offset + 4], 16)
        CCCC = reverse_hex(insns[offset+4:offset+8])

        decodedInstruction.op = op
        decodedInstruction.vA = A
        decodedInstruction.vB = B
        decodedInstruction.vC = CCCC
        decodedInstruction.smaliCode = '%s v%d, v%d, %s // +%s' % (op, A, B, hex(int(offset/4)+int(CCCC, 16)), CCCC)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '22s':
        # Format: B|A|op CCCC <=> op vA, vB, #+CCCC
        op = '????'
        # (1) opcode=d0..d7 binop/lit16 vA, vB, #+CCCC
        if opcode >= 0xd0 and opcode <= 0xd7:
            ops = ['add-int/lit16', 'rsub-int', 'mul-int/lit16', 'div-int/lit16', 'rem-int/lit16', 'and-int/lit16', 'or-int/lit16', 'xor-int/lit16']
            op = ops[opcode - 0xd0]

        B = int(insns[offset + 2: offset + 3], 16)
        A = int(insns[offset + 3: offset + 4], 16)
        CCCC = reverse_hex(insns[offset + 4:offset + 8])

        decodedInstruction.op = op
        decodedInstruction.vA = A
        decodedInstruction.vB = B
        decodedInstruction.vC = int(CCCC, 16)
        decodedInstruction.smaliCode = '%s v%d, v%d, #+%s' % (op, A, B, CCCC)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '22c':
        # Format: B|A|op CCCC <=> op vA, vB, [type|field]@CCCC
        op = '????'
        indexType = '????'
        indexStr = ''

        B = int(insns[offset + 2:offset + 3], 16)
        A = int(insns[offset + 3:offset + 4], 16)
        CCCC = reverse_hex(insns[offset + 4:offset + 8])

        # (1) opcode=20 instance-of vA, vB, type@CCCC
        if opcode == 0x20:
            op = 'instance-of'
            indexType = 'type'
            indexStr = dexFile.DexTypeIdList[int(CCCC, 16)]
        # (2) opcode=23 new-array vA, vB, type@CCCC
        if opcode == 0x23:
            op = 'new-array'
            indexType = 'type'
            indexStr = dexFile.DexTypeIdList[int(CCCC, 16)]
        # (3) opcode=52..5f iinstanceop vA, vB, field@CCCC
        if opcode >= 0x52 and opcode <= 0x5f:
            iinstanceop = ['iget', 'iget-wide', 'iget-object', 'iget-boolean', 'iget-byte', 'iget-char', 'iget-short',
                           'iput', 'iput-wide', 'iput-object', 'iput-boolean', 'iput-byte', 'iput-char', 'put-short']
            op = iinstanceop[opcode - 0x52]
            indexType = 'field'
            dexFieldIdObj = dexFile.DexFieldIdList[int(CCCC, 16)]
            indexStr = dexFieldIdObj.toString(dexFile)

        decodedInstruction.op = op
        decodedInstruction.vA = A
        decodedInstruction.vB = B
        decodedInstruction.vC = int(CCCC, 16)
        decodedInstruction.indexType = indexType
        decodedInstruction.smaliCode = '%s v%d, v%d %s@%s //%s' % (op, A, B, indexType, CCCC, indexStr)
        decodedInstruction.offset = offset
        decodedInstruction.length = 8

    elif formatIns == '22cs':
        # Format: B|A|op CCCC <=> op vA, vB, fieldoff@CCCC
        # 无opcode
        pass
    elif formatIns == '30t':
        # Format: ØØ|op AAAAlo AAAAhi <=> op +AAAAAAAA
        # (1) opcode=2a goto/32 +AAAAAAAA
        if opcode == 0x2a:
            AAAAAAAA = reverse_hex(insns[offset + 2:offset + 12])
            buma = word_to_buma(int(reverse_hex(insns[offset + 4:offset + 12]), 16))

            decodedInstruction.op = 'goto/32'
            decodedInstruction.vA = int(AAAAAAAA, 16)
            decodedInstruction.smaliCode = 'goto/32 %s //%s' % (hex(int(offset/4)+buma), hex(buma))
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

    elif formatIns == '32x':
        # Format: ØØ|op AAAA BBBB <=> op vAAAA, vBBBB
        op = '????'
        # (1) opcode=03 move/16 vAAAA, vBBBB
        # (2) opcode=06 move-wide/16 vAAAA, vBBBB
        # (3) opcode=09 move-object/16 vAAAA, vBBBB
        if opcode == 0x03:
            op = 'move/16'
        if opcode == 0x06:
            op = 'move-wide/16'
        if opcode == 0x09:
            op = 'move-object/16'
        AAAA = reverse_hex(insns[offset + 2:offset + 6])
        BBBB = reverse_hex(insns[offset + 6:offset + 10])

        decodedInstruction.op = op
        decodedInstruction.vA = int(AAAA, 16)
        decodedInstruction.vB = int(BBBB, 16)
        decodedInstruction.smaliCode = '%s v%s, v%s' % (op, AAAA, BBBB)
        decodedInstruction.offset = offset
        decodedInstruction.length = 10

    elif formatIns == '31i':
        # Format: AA|op BBBBlo BBBBhi <=> op vAA, #+BBBBBBBB
        op = '????'
        # (1) opcode=14 const vAA, #+BBBBBBBB
        if opcode == 0x14:
            op = 'const'
        # (2) opcode=17 const-wide/32 vAA, #+BBBBBBBB
        if opcode == 0x17:
            op = 'const-wide/32'

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBBBBBB = reverse_hex(insns[offset + 4:offset + 12])

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = int(BBBBBBBB, 16)
        decodedInstruction.smaliCode = '%s v%d, #+%s' % (op, AA, BBBBBBBB)
        decodedInstruction.offset = offset
        decodedInstruction.length = 12

    elif formatIns == '31t':
        # Format: AA|op BBBBlo BBBBhi <=> op vAA, +BBBBBBBB
        op = '????'
        # (1) opcode=26 fill-array-data vAA, +BBBBBBBB
        # (2) opcode=2b packed-switch vAA, +BBBBBBBB
        # (3) opcode=2c sparse-switch vAA, +BBBBBBBB
        if opcode == 0x26:
            op = 'fill-array-data'
        if opcode == 0x2b:
            op = 'packed-switch'
        if opcode == 0x2c:
            op = 'sparse-switch'

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBBBBBB = reverse_hex(insns[offset + 4:offset + 12])
        pseudo_instructions_offset = int(int(BBBBBBBB, 16) + byteCounts)
        retVal = parsePseudoInstruction(byteCounts, insns, pseudo_instructions_offset * 4)

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = int(BBBBBBBB, 16)
        decodedInstruction.smaliCode = '%s v%d, %08x // +%s, %s' % (op, AA, pseudo_instructions_offset, BBBBBBBB, retVal)
        decodedInstruction.offset = offset
        decodedInstruction.length = 12

    elif formatIns == '31c':
        # Format: AA|op BBBBlo BBBBhi <=> op vAA, thing@BBBBBBBB
        op = '????'
        indexStr = ''

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBBBBBB = reverse_hex(insns[offset + 4:offset + 12])

        # (1) opcode=1b const-string/jumbo vAA, string@BBBBBBBB
        if opcode == 0x1b:
            op = 'const-string/jumbo'
            indexStr = dexFile.DexStringIdList[int(BBBBBBBB, 16)]

            decodedInstruction.op = op
            decodedInstruction.vA = AA
            decodedInstruction.vB = BBBBBBBB
            decodedInstruction.smaliCode = '%s v%d, string@%s //%s' % (op, AA, BBBBBBBB, indexStr)
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

    elif formatIns == '35c':
        # Format: A|G|op BBBB F|E|D|C
        indexType = '????'
        op = '????'
        indexStr = ''

        A = int(insns[offset + 2:offset + 3], 16)
        G = int(insns[offset + 3:offset + 4], 16)
        BBBB = reverse_hex(insns[offset + 4:offset + 8])

        registerStr = reverse_hex(insns[offset + 8:offset + 12])
        F = int(registerStr[:1], 16)
        E = int(registerStr[1:2], 16)
        D = int(registerStr[2:3], 16)
        C = int(registerStr[3:4], 16)

        # (1) opcode=24 filled-new-array {vC, vD, vE, vF, vG}, type@BBBB
        if opcode == 0x24:
            op = 'filled-new-array'
            indexType = 'type'
            indexStr = dexFile.DexTypeIdList[int(BBBB, 16)]
        # (2) opcode=62..72 invoke-kind {vC, vD, vE, vF, vG}, method@BBBB
        if opcode >= 0x6e and opcode <= 0x72:
            invoke_kind = ['invoke-virtual', 'invoke-super', 'invoke-direct', 'invoke-static', 'invoke-interface']
            op = invoke_kind[opcode-0x6e]
            indexType = 'method'

            dexMethodIdObj = dexFile.DexMethodIdList[int(BBBB, 16)]
            indexStr = dexMethodIdObj.toString(dexFile)
            decodedInstruction.getApi = dexMethodIdObj.toApi(dexFile)

        registers = None
        if A == 0:  # [A=0] op {}, kind@BBBB
            decodedInstruction.op = op
            decodedInstruction.vA = A
            decodedInstruction.vB = int(BBBB, 16)
            decodedInstruction.indexType = indexType
            decodedInstruction.smaliCode = '%s {}, %s@%s //%s' % (op, indexType, BBBB, indexStr)
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

        elif A == 1:  # [A=1] op {vC}, kind@BBBB
            decodedInstruction.op = op
            decodedInstruction.vA = A
            decodedInstruction.vB = int(BBBB, 16)
            decodedInstruction.vC = C
            decodedInstruction.indexType = indexType
            decodedInstruction.smaliCode = '%s {v%d}, %s@%s //%s' % (op, C, indexType, BBBB, indexStr)
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

        elif A == 2:  # [A=2] op {vC, vD}, kind@BBBB
            decodedInstruction.op = op
            decodedInstruction.vA = A
            decodedInstruction.vB = int(BBBB, 16)
            decodedInstruction.vC = C
            decodedInstruction.vD = D
            decodedInstruction.indexType = indexType
            decodedInstruction.smaliCode = '%s {v%d, v%d}, %s@%s //%s' % (op, C, D, indexType, BBBB, indexStr)
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

        elif A == 3:  # [A=3] op {vC, vD, vE}, kind@BBBB
            decodedInstruction.op = op
            decodedInstruction.vA = A
            decodedInstruction.vB = int(BBBB, 16)
            decodedInstruction.vC = C
            decodedInstruction.vD = D
            decodedInstruction.vE = E
            decodedInstruction.indexType = indexType
            decodedInstruction.smaliCode = '%s {v%d, v%d, v%d}, %s@%s //%s' % (op, C, D, E, indexType, BBBB, indexStr)
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

        elif A == 4:  # [A=4] op {vC, vD, vE, vF}, kind@BBBB
            decodedInstruction.op = op
            decodedInstruction.vA = A
            decodedInstruction.vB = int(BBBB, 16)
            decodedInstruction.vC = C
            decodedInstruction.vD = D
            decodedInstruction.vE = E
            decodedInstruction.vF = F
            decodedInstruction.indexType = indexType
            decodedInstruction.smaliCode = '%s {v%d, v%d, v%d, v%d}, %s@%s //%s' % (op, C, D, E, F, indexType, BBBB, indexStr)
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

        elif A == 5:  # [A=5] op {vC, vD, vE, vF, vG}, type@BBBB
            decodedInstruction.op = op
            decodedInstruction.vA = A
            decodedInstruction.vB = int(BBBB, 16)
            decodedInstruction.vC = C
            decodedInstruction.vD = D
            decodedInstruction.vE = E
            decodedInstruction.vF = F
            decodedInstruction.vG = G
            decodedInstruction.indexType = indexType
            decodedInstruction.smaliCode = '%s {v%d, v%d, v%d, v%d, %d}, %s@%s //%s' % (op, C, D, E, F, G, indexType, BBBB, indexStr)
            decodedInstruction.offset = offset
            decodedInstruction.length = 12

    elif formatIns == '35ms':
        # Format: A|G|op BBBB F|E|D|C
        # 无opcode
        pass

    elif formatIns == '35mi':
        # Format: A|G|op BBBB F|E|D|C
        # 无opcode
        pass

    elif formatIns == '3rc':
        # Format: AA|op BBBB CCCC <=> op {vCCCC .. vNNNN} [method|type]@BBBB
        op = '????'
        indexType = '????'
        indexStr = ''

        AA = int(insns[offset + 2:offset + 4], 16)
        BBBB = reverse_hex(insns[offset + 4:offset + 8])
        CCCC = int(reverse_hex(insns[offset + 8:offset + 12]), 16)
        N = AA + CCCC - 1

        # (1) opcode=25 filled-new-array/range {vCCCC .. vNNNN}, type@BBBB
        if opcode == 0x25:
            op = 'fiiled-new-array/range'
            indexType = 'type'
            indexStr = dexFile.DexTypeIdList[int(BBBB, 16)]
        # (2) opcode=74..78 invoke-kind/range {vCCCC .. vNNNN}, method@BBBB
        if opcode >= 0x74 and opcode <= 0x78:
            ops = ['invoke-virtual/range', 'invoke-super/range', 'invoke-direct/range', 'invoke-static/range', 'invoke-intenrface/range']
            op = ops[opcode - 0x74]
            indexType = 'method'
            dexMethodIdObj = dexFile.DexMethodIdList[int(BBBB, 16)]
            indexStr = dexMethodIdObj.toString(dexFile)

        registers = ''
        for i in range(N):
            registers += 'v' + str(CCCC + i) + ','

        decodedInstruction.op = op
        decodedInstruction.vA = AA
        decodedInstruction.vB = int(BBBB, 16)
        decodedInstruction.vC = CCCC
        decodedInstruction.indexType = indexType
        decodedInstruction.smaliCode = '%s {%s} %s@%s //%s' % (op, registers, indexType, BBBB, indexStr)
        decodedInstruction.offset = offset
        decodedInstruction.length = 12

    elif formatIns == '3rms':
        # Format: AA|op BBBB CCCC <=> op {vCCCC .. vNNNN}, vtaboff@BBBB
        # 无opcode
        pass
    elif formatIns == '3rmi':
        # Format: AA|op BBBB CCCC <=> op {vCCCC .. vNNNN}, inline@BBBB
        # 无opcode
        pass
    elif formatIns == '51l':
        # Format: AA|op BBBBlo BBBB BBBB BBBBhi <=>op vAA,#+BBBBBBBBBBBBBBBB
        # (1) opcode=18 const-wide vAA, #+BBBBBBBBBBBBBBBB
        if opcode == 0x18:
            AA = int(insns[offset+2:offset+4], 16)
            BBBBBBBBBBBBBBBB = reverse_hex(insns[offset+4:offset+20])

            decodedInstruction.op = 'const-wide'
            decodedInstruction.vA = AA
            decodedInstruction.vB = int(BBBBBBBBBBBBBBBB, 16)
            decodedInstruction.smaliCode = 'const-wide v%d, #+%s' % (AA, BBBBBBBBBBBBBBBB)
            decodedInstruction.offset = offset
            decodedInstruction.length = 20


    elif formatIns == '33x':
        # Format: exop BB|AA CCCC <=> exop vAA, vBB, vCCCC
        # 无opcode
        pass
    elif formatIns == '32s':
        # Format: exop BB|AA CCCC <=> exop vAA, vBB, #+CCCC
        # 无opcode
        pass
    elif formatIns == '40sc':
        # Format: exop BBBBlo BBBBhi AAAA <=> exop AAAA, kind@BBBBBBBB
        # 无opcode
        pass

    '''
    expaneded opcode
    opcode为ff，表示后面还有二级opcode
    '''
    if opcode == 0xff:
        expanded_opcode = int(reverse_hex(insns[offset:offset + 4]), 16)
        formatIns, _ = getOpCode(expanded_opcode)

    if formatIns == '41c':
        expanded_opcode = int(reverse_hex(insns[offset:offset + 4]), 16)
        # Format: exop BBBBlo BBBBhi AAAA <=> exop vAAAA, [field|type]@BBBBBBBB
        indexType = '????'
        op = '????'
        # (1) expanded_opcode=00ff const-class/jumbo vAAAA, type@BBBBBBBB
        if expanded_opcode == 0x00ff:
            op = 'const-class/jumbo'
            indexType = 'type'
        # (2) expanded_opcode=01ff check-cast/jumbo vAAAA, type@BBBBBBBB
        elif expanded_opcode == 0x01ff:
            op = 'check-cast/jumbo'
            indexType = 'type'
        # (3) expanded_opcode=03ff new-instance/jumbo vAAAA, type@BBBBBBBB
        elif expanded_opcode == 0x03ff:
            op = 'new-instance/jumbo'
            indexType = 'type'
        # (4) expanded_opcode=14ff..21ff sstaticop/jumbo vAAAA, field@BBBBBBBB
        elif expanded_opcode >= 0x14ff and expanded_opcode <= 0x21ff:
            ops = ['sget/jumbo', 'sget-wide/jumbo', 'sget-object/jumbo', 'sget-boolean/jumbo', 'sget-byte/jumbo',
                   'sget-char/jumbo', 'sget-short/jumbo', 'sput/jumbo', 'sput-wide/jumbo', 'sput-object/jumbo',
                   'sput-boolean/jumbo', 'sput-byte/jumbo', 'sput-char/jumbo', 'sput-short/jumbo']
            op = ops[expanded_opcode - 0x14ff]
            indexType = 'field'

        BBBBBBBB = int(reverse_hex(insns[offset + 4:offset + 12]), 16)
        AAAA = int(reverse_hex(insns[offset + 12:offset + 16]), 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AAAA
        decodedInstruction.vB = BBBBBBBB
        decodedInstruction.indexType = indexType
        decodedInstruction.smaliCode = '%s v%d, %s@%s' % (op, AAAA, indexType, hex(BBBBBBBB)[2:])
        decodedInstruction.offset = offset
        decodedInstruction.length = 16

    elif formatIns == '52c':
        expanded_opcode = int(reverse_hex(insns[offset:offset + 4]), 16)
        indexType = '????'
        op = '????'
        # Format: exop CCCClo CCCChi AAAA BBBB <=> exop vAAAA, vBBBB, [field|type]@CCCCCCCC
        # (1) expanded_opcode=02ff instance-of/jumbo vAAAA, vBBBB, type@CCCCCCCC
        if expanded_opcode == 0x02ff:
            op = 'instance-of/jumbo'
            indexType = 'type'
        # (2) expanded_opcode=04ff new-array/jumbo vAAAA, vBBBB, type@CCCCCCCC
        if expanded_opcode == 0x02ff:
            op = 'new-array/jumbo'
            indexType = 'type'
        # (3) expanded_opcode=06ff..13ff 	iinstanceop/jumbo vAAAA, vBBBB, field@CCCCCCCC
        if expanded_opcode >= 0x06ff and expanded_opcode <= 0x13ff:
            ops = ['iget/jumbo', 'iget-wide/jumbo', 'iget-object/jumbo', 'iget-boolean/jumbo', 'iget-byte/jumbo',
                   'iget-char/jumbo', 'iget-short/jumbo', 'iput/jumbo', 'iput-wide/jumbo', 'iput-object/jumbo',
                   'iput-boolean/jumbo', 'iput-byte/jumbo', 'iput-char/jumbo', 'iput-short/jumbo']
            op = ops[expanded_opcode - 0x06ff]
            indexType = 'field'
        CCCCCCCC = int(reverse_hex(insns[offset + 4:offset + 12]), 16)
        AAAA = int(reverse_hex(insns[offset + 12:offset + 16]), 16)
        BBBB = int(reverse_hex(insns[offset + 16:offset + 20]), 16)

        decodedInstruction.op = op
        decodedInstruction.vA = AAAA
        decodedInstruction.vB = BBBB
        decodedInstruction.vC = CCCCCCCC
        decodedInstruction.indexType = indexType
        decodedInstruction.smaliCode = '%s v%d, v%d %s@%s' % (op, AAAA, BBBB, indexType, hex(CCCCCCCC)[2:])
        decodedInstruction.offset = offset
        decodedInstruction.length = 20

    elif formatIns == '5rc':
        expanded_opcode = int(reverse_hex(insns[offset:offset + 4]), 16)
        indexType = '????'
        op = '????'
        # Format: exop BBBBlo BBBBhi AAAA CCCC <=> exop {vCCCC .. vNNNN}, [method|type]@BBBBBBBB
        # (1) expanded_opcode=05ff filled-new-array/jumbo {vCCCC .. vNNNN}, type@BBBBBBBB
        if expanded_opcode == 0x05ff:
            op = 'filled-new-array/jumbo'
            indexType = 'type'
        # (2) expanded_opcode=22ff..26ff invoke-kind/jumbo {vCCCC .. vNNNN}, method@BBBBBBBB
        if expanded_opcode >= 0x22ff and expanded_opcode <= 0x26ff:
            ops= ['invoke-virtual/jumbo', 'invoke-super/jumbo', 'invoke-direct/jumbo',
                  'invoke-static/jumbo', 'invoke-interface/jumbo']
            op = ops[expanded_opcode - 0x22ff]
            indexType = 'method'
        BBBBBBBB = int(reverse_hex(insns[offset + 4:offset + 12]), 16)
        AAAA = int(reverse_hex(insns[offset + 12:offset + 16]), 16)
        CCCC = int(reverse_hex(insns[offset + 16:offset + 20]), 16)
        N = AAAA + CCCC - 1

        registers = ''
        for i in range(N):
            registers += 'v' + str(CCCC + i) + ','

        decodedInstruction.op = op
        decodedInstruction.vA = AAAA
        decodedInstruction.vB = BBBBBBBB
        decodedInstruction.vC = CCCC
        decodedInstruction.indexType = indexType
        decodedInstruction.smaliCode = '%s {%s} %s@%s' % (op, registers, indexType, hex(BBBBBBBB)[2:])
        decodedInstruction.offset = offset
        decodedInstruction.length = 20

    return decodedInstruction

def parsePseudoInstruction(opcode_address, insns, offset):
    offset = int(offset)
    ident = reverse_hex(insns[offset:offset+4])
    # packed-switch-payload Format
    if ident == '0100':
        size = int(reverse_hex(insns[offset + 4:offset + 8]), 16)
        first_key = int(reverse_hex(insns[offset+8:offset+16]), 16)
        targets = []
        sb = ''
        for i in range(size):
            _v = int(reverse_hex(insns[offset+16+8*i:offset+16+8*(i+1)]), 16)
            targets.append(_v)
            sb += '    \t%-16scase %d: goto %s\n' % ('', first_key+i, hex(_v + opcode_address))
        return '\n'+sb
    # sparse-switch-payload Format
    if ident == '0200':
        size = int(reverse_hex(insns[offset + 4:offset + 8]), 16)
        keys = []
        targets = []
        sb = ''
        for i in range(size):
            keys.append(int(reverse_hex(insns[offset+8+8*i:offset+8+8*(i+1)]), 16))
            _v = int(reverse_hex(insns[(offset+8+8*i)+size*8:(offset+8+8*(i+1))+size*8]), 16)

            hexNum = _v + opcode_address
            if hexNum > (0xffffffff+1):
                hexNum -= 0xffffffff+1
                tmp = hex(hexNum)
                if tmp.endswith('L'):
                    tmp = tmp[:-1]
                targets.append(tmp)
            else:
                targets.append(hex(hexNum))
            sb += '    \t%-16scase %d: goto %s\n' % ('', keys[i], targets[i])
        return '\n'+sb
    # fill-array-data-payload Format
    if ident == '0300':
        element_width = int(reverse_hex(insns[offset + 4:offset + 8]), 16)
        size = int(reverse_hex(insns[offset + 8:offset + 16]), 16)
        data = []

        dataStr = '['
        for i in range(size):
            val = insns[offset + 16 + 2*element_width*i:offset + 16 + 2*element_width*(i+1)]
            data.append(val)
            dataStr += val + ','
        dataStr += ']'
        return dataStr


MAP_ITEM_TYPE_CODES = {
    0x0000 : "kDexTypeHeaderItem",
    0x0001 : "kDexTypeStringIdItem",
    0x0002 : "kDexTypeTypeIdItem",
    0x0003 : "kDexTypeProtoIdItem",
    0x0004 : "kDexTypeFieldIdItem",
    0x0005 : "kDexTypeMethodIdItem",
    0x0006 : "kDexTypeClassDefItem",
    0x1000 : "kDexTypeMapList",
    0x1001 : "kDexTypeTypeList",
    0x1002 : "kDexTypeAnnotationSetRefList",
    0x1003 : "kDexTypeAnnotationSetItem",
    0x2000 : "kDexTypeClassDataItem",
    0x2001 : "kDexTypeCodeItem",
    0x2002 : "kDexTypeStringDataItem",
    0x2003 : "kDexTypeDebugInfoItem",
    0x2004 : "kDexTypeAnnotationItem",
    0x2005 : "kDexTypeEncodedArrayItem",
    0x2006 : "kDexTypeAnnotationsDirectoryItem",
}


class DexFile(object):
    """docstring for DexFile"""
    def __init__(self, filepath):
        super(DexFile, self).__init__()
        self.filepath = filepath
        # Dex文件头部
        self.DexHeader = DexHeader()
        # 字符串索引区
        self.DexStringIdList = []
        # 类型索引区
        self.DexTypeIdList = []
        # 字段索引区
        self.DexFieldIdList = []
        # 原型索引区
        self.DexProtoIdList = []
        # 方法索引区
        self.DexMethodIdList = []
        # 类定义区
        self.dexClassDefList = []

        self.init_header(self.filepath) # 初始化dex header
        self.init_DexStringId() # 初始化 DexStringId index table
        self.init_DexTypeId() # 初始化DexTypeId index table
        self.init_DexProtoId() # 初始化DexProtoId index table
        self.int_DexFieldId() # 初始化DexFieldId index table
        self.init_DexMethodId() # 初始化DexMethodId index table
        self.init_DexClassDef() # 初始化DexClassDef类定义区


    def init_header(self, filepath):
        f = open(filepath, "rb")

        self.DexHeader.f = f

        # 1) 读取 magic (8字节)
        f.seek(0x0, 0)
        magic_bytes = safe_read(f, 8)
        if magic_bytes is None:
            print("[init_header] Not enough bytes for 'magic', file might be truncated.")
            return
        self.DexHeader.magic = binascii.b2a_hex(magic_bytes)

        # 2) 读取 checksum (4字节)
        f.seek(0x8, 0)
        csum_bytes = safe_read(f, 4)
        if csum_bytes is None:
            print("[init_header] Not enough bytes for 'checksum'.")
            return
        self.DexHeader.checksum = reverse_hex(binascii.b2a_hex(csum_bytes))

        # 3) 读取 signature (20字节)
        f.seek(0xc, 0)
        sig_bytes = safe_read(f, 20)
        if sig_bytes is None:
            print("[init_header] Not enough bytes for 'signature'.")
            return
        self.DexHeader.signature = binascii.b2a_hex(sig_bytes)

        # 4) 读取 file_size (4字节)
        f.seek(0x20, 0)
        fs_bytes = safe_read(f, 4)
        if fs_bytes:
            self.DexHeader.file_size = reverse_hex(binascii.b2a_hex(fs_bytes))

        # 5) 读取 header_size (4字节)
        f.seek(0x24, 0)
        hdr_bytes = safe_read(f, 4)
        if hdr_bytes:
            self.DexHeader.header_size = reverse_hex(binascii.b2a_hex(hdr_bytes))

        # 6) 读取 endian_tag (4字节)
        f.seek(0x28, 0)
        endian_bytes = safe_read(f, 4)
        if endian_bytes:
            self.DexHeader.endian_tag = reverse_hex(binascii.b2a_hex(endian_bytes))

        # 7) 读取 link_size (4字节)
        f.seek(0x2c, 0)
        link_size_bytes = safe_read(f, 4)
        if link_size_bytes:
            self.DexHeader.link_size = reverse_hex(binascii.b2a_hex(link_size_bytes))

        # 8) 读取 link_off (4字节)
        f.seek(0x30, 0)
        link_off_bytes = safe_read(f, 4)
        if link_off_bytes:
            self.DexHeader.link_off = reverse_hex(binascii.b2a_hex(link_off_bytes))

        # 9) 读取 map_off (4字节)
        f.seek(0x34, 0)
        map_off_bytes = safe_read(f, 4)
        if map_off_bytes:
            self.DexHeader.map_off = reverse_hex(binascii.b2a_hex(map_off_bytes))

        f.seek(0x38, 0)
        string_ids_size_bytes = safe_read(f, 4)
        if string_ids_size_bytes:
            self.DexHeader.string_ids_size = reverse_hex(binascii.b2a_hex(string_ids_size_bytes))

        f.seek(0x3c, 0)
        string_ids_off_bytes = safe_read(f, 4)
        if string_ids_off_bytes:
            self.DexHeader.string_ids_off = reverse_hex(binascii.b2a_hex(string_ids_off_bytes))

        f.seek(0x40, 0)
        type_ids_size_bytes = safe_read(f, 4)
        if type_ids_size_bytes:
            self.DexHeader.type_ids_size = reverse_hex(binascii.b2a_hex(type_ids_size_bytes))

        f.seek(0x44, 0)
        type_ids_off_bytes = safe_read(f, 4)
        if type_ids_off_bytes:
            self.DexHeader.type_ids_off = reverse_hex(binascii.b2a_hex(type_ids_off_bytes))

        f.seek(0x48, 0)
        proto_ids_size_bytes = safe_read(f, 4)
        if proto_ids_size_bytes:
            self.DexHeader.proto_ids_size = reverse_hex(binascii.b2a_hex(proto_ids_size_bytes))

        f.seek(0x4c, 0)
        proto_ids_off_bytes = safe_read(f, 4)
        if proto_ids_off_bytes:
            self.DexHeader.proto_ids_off = reverse_hex(binascii.b2a_hex(proto_ids_off_bytes))

        f.seek(0x50, 0)
        field_ids_size_bytes = safe_read(f, 4)
        if field_ids_size_bytes:
            self.DexHeader.field_ids_size = reverse_hex(binascii.b2a_hex(field_ids_size_bytes))

        f.seek(0x54, 0)
        field_ids_off_bytes = safe_read(f, 4)
        if field_ids_off_bytes:
            self.DexHeader.field_ids_off = reverse_hex(binascii.b2a_hex(field_ids_off_bytes))

        f.seek(0x58, 0)
        method_ids_size_bytes = safe_read(f, 4)
        if method_ids_size_bytes:
            self.DexHeader.method_ids_size = reverse_hex(binascii.b2a_hex(method_ids_size_bytes))

        f.seek(0x5c, 0)
        method_ids_off_bytes = safe_read(f, 4)
        if method_ids_off_bytes:
            self.DexHeader.method_ids_off = reverse_hex(binascii.b2a_hex(method_ids_off_bytes))

        f.seek(0x60, 0)
        class_defs_size_bytes = safe_read(f, 4)
        if class_defs_size_bytes:
            self.DexHeader.class_defs_size = reverse_hex(binascii.b2a_hex(class_defs_size_bytes))

        f.seek(0x64, 0)
        class_defs_off_bytes = safe_read(f, 4)
        if class_defs_off_bytes:
            self.DexHeader.class_defs_off = reverse_hex(binascii.b2a_hex(class_defs_off_bytes))

        f.seek(0x68, 0)
        data_size_bytes = safe_read(f, 4)
        if data_size_bytes:
            self.DexHeader.data_size = reverse_hex(binascii.b2a_hex(data_size_bytes))

        f.seek(0x6c, 0)
        data_off_bytes = safe_read(f, 4)
        if data_off_bytes:
            self.DexHeader.data_off = reverse_hex(binascii.b2a_hex(data_off_bytes))

    def print_header(self):
        print('[+] magiD:\t0x' + self.DexHeader.magic)
        print('[+] checksum:\t0x' + self.DexHeader.checksum)
        print('[+] signature:\t' + self.DexHeader.signature)
        print('[+] file_size:\t0x' + self.DexHeader.file_size)
        print('[+] header_size:\t0x' + self.DexHeader.header_size)
        print('[+] endian_tag:\t0x' + self.DexHeader.endian_tag)
        print('[+] link_size:\t0x' + self.DexHeader.link_size)
        print('[+] link_off:\t0x' + self.DexHeader.link_off)
        print('[+] map_off:\t0x' + self.DexHeader.map_off)
        print('[+] string_ids_size:\t0x' + self.DexHeader.string_ids_size)
        print('[+] string_ids_off:\t0x' + self.DexHeader.string_ids_off)
        print('[+] type_ids_size:\t0x' + self.DexHeader.type_ids_size)
        print('[+] type_ids_off:\t0x' + self.DexHeader.type_ids_off)
        print('[+] proto_ids_size:\t0x' + self.DexHeader.proto_ids_size)
        print('[+] proto_ids_off:\t0x' + self.DexHeader.proto_ids_off)
        print('[+] field_ids_size:\t0x' + self.DexHeader.field_ids_size)
        print('[+] field_ids_off:\t0x' + self.DexHeader.field_ids_off)
        print('[+] method_ids_size:\t0x' + self.DexHeader.method_ids_size)
        print('[+] method_ids_off:\t0x' + self.DexHeader.method_ids_off)
        print('[+] class_defs_size:\t0x' + self.DexHeader.class_defs_size)
        print('[+] class_defs_off:\t0x' + self.DexHeader.class_defs_off)
        print('[+] data_size:\t0x' + self.DexHeader.data_size)
        print('[+] data_off:\t0x' + self.DexHeader.data_off)

    def print_DexMapList(self):
        map_off_int = int(self.DexHeader.map_off or '0', 16)
        if map_off_int == 0:
            print("[print_DexMapList] map_off=0, skip.")
            return

        self.DexHeader.f.seek(map_off_int, 0)
        size_bytes = safe_read(self.DexHeader.f, 4)
        if size_bytes is None:
            print("[print_DexMapList] Not enough data to read 'size', skip.")
            return

        size_hex = reverse_hex(binascii.b2a_hex(size_bytes))
        size = int(size_hex, 16)

        for index in range(size):
            self.print_DexMapItem(map_off_int + 4, index)


    def print_DexMapItem(self, map_off, index):
        item_off = map_off + index * 12
        self.DexHeader.f.seek(item_off, 0)

        # 1) type (u2)
        type_bytes = safe_read(self.DexHeader.f, 2)
        if type_bytes is None:
            print("[print_DexMapItem] Not enough data for 'type', skip.")
            return
        dexType = reverse_hex(binascii.b2a_hex(type_bytes))

        # 2) unused (u2)
        unused_bytes = safe_read(self.DexHeader.f, 2)
        if unused_bytes is None:
            print("[print_DexMapItem] Not enough data for 'unused', skip.")
            return
        unused_hex = reverse_hex(binascii.b2a_hex(unused_bytes))

        # 3) size (u4)
        size_bytes = safe_read(self.DexHeader.f, 4)
        if size_bytes is None:
            print("[print_DexMapItem] Not enough data for 'size', skip.")
            return
        size_hex = reverse_hex(binascii.b2a_hex(size_bytes))

        # 4) offset (u4)
        offset_bytes = safe_read(self.DexHeader.f, 4)
        if offset_bytes is None:
            print("[print_DexMapItem] Not enough data for 'offset', skip.")
            return
        offset_hex = reverse_hex(binascii.b2a_hex(offset_bytes))

        type_int = int(dexType, 16)
        type_str = MAP_ITEM_TYPE_CODES.get(type_int, "Unknown")

        print('\n')
        print(f'[+] #{index} DexMapItem:')
        print(f'    u2 dexType = {dexType}  #{type_str}')
        print(f'    u2 unused  = {unused_hex}')
        print(f'    u4 size    = {size_hex}')
        print(f'    u4 offset  = {offset_hex}')


    def init_DexStringId(self):
        """
        typedef struct DexStringId {
            u4  stringDataOff;      /* file offset to string_data_item */
        } DexStringId;
        """
        string_ids_off_int = int(self.DexHeader.string_ids_off, 16)
        string_ids_size_int = int(self.DexHeader.string_ids_size, 16)

        for index in range(string_ids_size_int):
            # 1) 先定位到 string_ids_off_int + index*4
            self.DexHeader.f.seek(string_ids_off_int + index*4, 0)

            # 2) 尝试读 4 字节：stringDataOff
            offset_bytes = safe_read(self.DexHeader.f, 4)
            if offset_bytes is None:
                print(f"[init_DexStringId] Not enough bytes to read stringDataOff at index={index}, skip.")
                break  # 或 continue，看你需求；这里一般 break 就够了

            some_data = reverse_hex(binascii.b2a_hex(offset_bytes))

            try:
                string_data_off = int(some_data, 16)
            except:
                print('[init_DexStringId] Something is wrong with offset hex =', some_data)
                continue

            # 3) 跳转到 string_data_off
            self.DexHeader.f.seek(string_data_off, 0)

            # 4) 先读取字符串长度的第1个字节
            #    注意：它只是 “存储了变长长度” 的开头字节，但这里你原代码是直接读1字节然后再循环
            first_len_byte = safe_read(self.DexHeader.f, 1)
            if first_len_byte is None:
                print(f"[init_DexStringId] Not enough bytes to read first length byte at offset={string_data_off}, skip.")
                continue

            # 5) 然后继续读取，直到遇到 '\x00'
            length = 0
            try:
                while True:
                    b = safe_read(self.DexHeader.f, 1)
                    if b is None:
                        print(f"[init_DexStringId] Reached EOF while reading string content, skip this string.")
                        break
                    # 把单字节 b 转成 int
                    val = int(reverse_hex(binascii.b2a_hex(b)), 16)
                    if val == 0:
                        # 遇到 \x00 就结束
                        break
                    length += 1
            except:
                print('[init_DexStringId] Something went wrong in reading string body.')
                break

            # 6) 回退到 string_data_off + 1，再次读出 length 长度的数据
            self.DexHeader.f.seek(string_data_off + 1, 0)
            real_str_bytes = safe_read(self.DexHeader.f, length)
            if real_str_bytes is None:
                print(f"[init_DexStringId] Not enough bytes to read the actual string (length={length}). skip.")
                continue

            # 再读 1 字节移除 \x00
            discard_null = safe_read(self.DexHeader.f, 1)
            if discard_null is None:
                print("[init_DexStringId] No trailing null byte, skip.")
                continue

            # 7) 尝试 decode
            try:
                dex_str_string = real_str_bytes.decode()
            except:
                dex_str_string = ''

            self.DexStringIdList.append(dex_str_string)


    def print_DexStringId(self):

        print('\n')
        print('[+] DexStringId:')
        for index in range(len(self.DexStringIdList)):
            print('    #%s %s' % (hex(index), self.DexStringIdList[index]))

    def init_DexTypeId(self):
        type_ids_off_int = int(self.DexHeader.type_ids_off or '0', 16)
        type_ids_size_int = int(self.DexHeader.type_ids_size or '0', 16)
        f = self.DexHeader.f

        f.seek(type_ids_off_int, 0)
        for i in range(type_ids_size_int):
            offset_bytes = safe_read(f, 4)
            if offset_bytes is None:
                print(f"[init_DexTypeId] Not enough data at index={i}, break.")
                break

            data_hex = reverse_hex(binascii.b2a_hex(offset_bytes))
            descriptor_idx = int(data_hex, 16)
            self.DexTypeIdList.append(descriptor_idx)


    def print_DexTypeId(self):
        print('\n')
        print('[+] DexTypeId:')
        for index in range(len(self.DexTypeIdList)):
            print('    #%s #%s' % (hex(index), self.getDexTypeId(index)))

    def init_DexProtoId(self):
        proto_ids_off_int = int(self.DexHeader.proto_ids_off or '0', 16)
        proto_ids_size_int = int(self.DexHeader.proto_ids_size or '0', 16)
        f = self.DexHeader.f

        for i in range(proto_ids_size_int):
            # ---- 1) 先读取 DexProtoId 的三个 u4 字段 ----
            f.seek(proto_ids_off_int + i*12, 0)

            # shortyIdx
            shorty_bytes = safe_read(f, 4)
            if shorty_bytes is None:
                print(f"[init_DexProtoId] Not enough data for shortyIdx at index={i}, break.")
                break
            shorty_hex = reverse_hex(binascii.b2a_hex(shorty_bytes))
            shortyIdx = int(shorty_hex, 16)

            # returnTypeIdx
            returnType_bytes = safe_read(f, 4)
            if returnType_bytes is None:
                print(f"[init_DexProtoId] Not enough data for returnTypeIdx at index={i}, break.")
                break
            returnType_hex = reverse_hex(binascii.b2a_hex(returnType_bytes))
            returnTypeIdx = int(returnType_hex, 16)

            # parametersOff
            parametersOff_bytes = safe_read(f, 4)
            if parametersOff_bytes is None:
                print(f"[init_DexProtoId] Not enough data for parametersOff at index={i}, break.")
                break
            parametersOff_hex = reverse_hex(binascii.b2a_hex(parametersOff_bytes))
            parametersOff = int(parametersOff_hex, 16)

            # 构造 DexProtoId 对象
            dexProtoIdObj = DexProtoId()
            dexProtoIdObj.shortyIdx = shortyIdx
            dexProtoIdObj.returnTypeIdx = returnTypeIdx
            dexProtoIdObj.parameterOff = parametersOff
            dexProtoIdObj.offset = proto_ids_off_int + i*12
            dexProtoIdObj.length = 12

            # ---- 2) 如果 parametersOff != 0, 解析 DexTypeList ----
            if parametersOff != 0:
                # 跳转到 parametersOff
                f.seek(parametersOff, 0)

                # 2.1) 先读 size (u4)
                size_bytes = safe_read(f, 4)
                if size_bytes is None:
                    print(f"[init_DexProtoId] Not enough data to read DexTypeList->size at offset=0x{parametersOff:x}.")
                    # 这里可以选择 break 或 continue
                    # break 会停止所有proto解析; continue 只会跳过此protoId
                    # 这里我选继续下一个 proto:
                    continue

                size_hex = reverse_hex(binascii.b2a_hex(size_bytes))
                type_list_size = int(size_hex, 16)

                # 构造 DexTypeList 对象
                dexTypeListObj = DexTypeList()
                dexTypeListObj.size = type_list_size

                # 2.2) 依次读取 type_list_size 个 DexTypeItem (每个 2字节 u2)
                for idx_type in range(type_list_size):
                    typeItem_bytes = safe_read(f, 2)
                    if typeItem_bytes is None:
                        print(f"[init_DexProtoId] Not enough data for DexTypeItem at index={idx_type}, offset=0x{parametersOff:x}.")
                        break
                    typeItem_hex = reverse_hex(binascii.b2a_hex(typeItem_bytes))
                    typeIdx_int = int(typeItem_hex, 16)
                    dexTypeListObj.list.append(typeIdx_int)

                # 将结果赋给 DexProtoId 对象
                dexProtoIdObj.dexTypeList = dexTypeListObj

            else:
                # 如果 parametersOff == 0, 说明无参数列表
                dexProtoIdObj.dexTypeList = None

            # ---- 3) 最后将解析结果放入 self.DexProtoIdList ----
            self.DexProtoIdList.append(dexProtoIdObj)


    def getDexStringId(self, shortyIdx):
        return self.DexStringIdList[shortyIdx]

    def getDexTypeId(self, returnTypeIdx):
        return self.DexStringIdList[self.DexTypeIdList[returnTypeIdx]]

    def print_DexProtoId(self):
        proto_ids_off_int = int(self.DexHeader.proto_ids_off, 16)
        self.DexHeader.f.seek(proto_ids_off_int, 0)
        print('\n')
        print('[+] DexProtoId:')
        for index in range(len(self.DexProtoIdList)):
            dexProtoidObj = self.DexProtoIdList[index]

            shortyIdxStr = self.getDexStringId(dexProtoidObj.shortyIdx)
            returnTypeIdxStr = self.getDexStringId(dexProtoidObj.returnTypeIdx)

            print('    #%s (%s~%s)' % (hex(index), hex(dexProtoidObj.offset), hex(dexProtoidObj.offset + dexProtoidObj.length)))
            print('    DexProtoId[%d]->shortyIdx= %s\t#%s' % (index,hex(dexProtoidObj.shortyIdx), shortyIdxStr))
            print('    DexProtoId[%d]->returnTypeIdx= %s\t#%s' % (index, hex(dexProtoidObj.returnTypeIdx), returnTypeIdxStr))
            print('    DexProtoId[%d]->parametersOff= %s' % (index, hex(dexProtoidObj.parameterOff)))
            if dexProtoidObj.dexTypeList:
                print('      DexTypeList->size= %s' % hex(dexProtoidObj.dexTypeList.size))
                for k in range(dexProtoidObj.dexTypeList.size):
                    print('      DexTypeList->list[%d]= %s\t#%s' % (k, hex(dexProtoidObj.dexTypeList.list[k]), self.getDexTypeId(dexProtoidObj.dexTypeList.list[k])))
            print('')

    def int_DexFieldId(self):
        field_ids_off = int(self.DexHeader.field_ids_off or '0', 16)
        field_ids_size = int(self.DexHeader.field_ids_size or '0', 16)
        f = self.DexHeader.f

        f.seek(field_ids_off, 0)
        for index in range(field_ids_size):
            # DexFieldId: u2 classIdx, u2 typeIdx, u4 nameIdx
            classIdx_bytes = safe_read(f, 2)
            if classIdx_bytes is None:
                print(f"[int_DexFieldId] Not enough data for classIdx at index={index}, break.")
                break
            classIdx_hex = reverse_hex(binascii.b2a_hex(classIdx_bytes))
            classIdx = int(classIdx_hex, 16)

            typeIdx_bytes = safe_read(f, 2)
            if typeIdx_bytes is None:
                print(f"[int_DexFieldId] Not enough data for typeIdx at index={index}, break.")
                break
            typeIdx_hex = reverse_hex(binascii.b2a_hex(typeIdx_bytes))
            typeIdx = int(typeIdx_hex, 16)

            nameIdx_bytes = safe_read(f, 4)
            if nameIdx_bytes is None:
                print(f"[int_DexFieldId] Not enough data for nameIdx at index={index}, break.")
                break
            nameIdx_hex = reverse_hex(binascii.b2a_hex(nameIdx_bytes))
            nameIdx = int(nameIdx_hex, 16)

            dexFieldIdObj = DexFieldId()
            dexFieldIdObj.classIdx = classIdx
            dexFieldIdObj.typeIdx = typeIdx
            dexFieldIdObj.nameIdx = nameIdx
            dexFieldIdObj.offset = field_ids_off + index * 8
            dexFieldIdObj.length = 8

            self.DexFieldIdList.append(dexFieldIdObj)

    def print_DexFieldId(self):
        print('[+] DexFieldId:')
        for index in range(len(self.DexFieldIdList)):
            self.DexHeader.f.seek(self.DexFieldIdList[index].offset, 0)
            # DexFieldId
            # u2 classIdx
            classIdx = self.DexFieldIdList[index].classIdx
            # u2 typeIdx
            typeIdx = self.DexFieldIdList[index].typeIdx
            # u4 nameIdx
            nameIdx = self.DexFieldIdList[index].nameIdx

            print('    #%s (%s~%s)' % (hex(index), hex(self.DexFieldIdList[index].offset), hex(self.DexFieldIdList[index].offset + self.DexFieldIdList[index].length)))
            print('    DexFieldId[%d]->classIdx=%s\t#%s' % (index, hex(classIdx), self.getDexStringId(classIdx)))
            print('    DexFieldId[%d]->typeIdx=%s\t#%s' % (index, hex(typeIdx), self.getDexStringId(typeIdx)))
            print('    DexFieldId[%d]->nameIdx=%s\t#%s' % (index, hex(nameIdx), self.getDexStringId(nameIdx)))
            print('')

    def init_DexMethodId(self):
        method_ids_off = int(self.DexHeader.method_ids_off or '0', 16)
        method_ids_size = int(self.DexHeader.method_ids_size or '0', 16)
        f = self.DexHeader.f

        f.seek(method_ids_off, 0)
        for index in range(method_ids_size):
            # DexMethodId: u2 classIdx, u2 protoIdx, u4 nameIdx
            classIdx_bytes = safe_read(f, 2)
            if classIdx_bytes is None:
                print(f"[init_DexMethodId] Not enough data for classIdx at index={index}, break.")
                break
            classIdx_hex = reverse_hex(binascii.b2a_hex(classIdx_bytes))
            classIdx = int(classIdx_hex, 16)

            protoIdx_bytes = safe_read(f, 2)
            if protoIdx_bytes is None:
                print(f"[init_DexMethodId] Not enough data for protoIdx at index={index}, break.")
                break
            protoIdx_hex = reverse_hex(binascii.b2a_hex(protoIdx_bytes))
            protoIdx = int(protoIdx_hex, 16)

            nameIdx_bytes = safe_read(f, 4)
            if nameIdx_bytes is None:
                print(f"[init_DexMethodId] Not enough data for nameIdx at index={index}, break.")
                break
            nameIdx_hex = reverse_hex(binascii.b2a_hex(nameIdx_bytes))
            nameIdx = int(nameIdx_hex, 16)

            dexMethodIdObj = DexMethodId()
            dexMethodIdObj.classIdx = classIdx
            dexMethodIdObj.protoIdx = protoIdx
            dexMethodIdObj.nameIdx = nameIdx
            dexMethodIdObj.offset = method_ids_off + index * 8
            dexMethodIdObj.length = 8

            self.DexMethodIdList.append(dexMethodIdObj)


    def print_DexMethodId(self):
        print('\n')
        print('[+] DexMethodId:')
        for index in range(len(self.DexMethodIdList)):
            # DexMethodId
            # u2 classIdx
            classIdx = self.DexMethodIdList[index].classIdx
            # u2 protoIdx
            protoIdx = self.DexMethodIdList[index].protoIdx
            # u4 nameIdx
            nameIdx = self.DexMethodIdList[index].nameIdx

            print('    #%s (%s~%s)' % (hex(index), hex(self.DexMethodIdList[index].offset), hex(self.DexMethodIdList[index].offset + self.DexMethodIdList[index].length)))
            print('    DexMethodId[%d]->classIdx=%s\t#%s' % (index, hex(classIdx), self.getDexTypeId(classIdx)))
            print('    DexMethodId[%d]->protoIdx=%s\t#%s' % (index, hex(protoIdx), self.DexProtoIdList[protoIdx].toString(self)))
            print('    DexMethodId[%d]->nameIdx =%s\t#%s' % (index, hex(nameIdx), self.DexStringIdList[nameIdx]))
            print('')

    def init_DexClassDef(self):
        """
        读取并解析 class_defs_size 个 DexClassDef 项目。
        每个 DexClassDef 有 32 字节（8 个 u4）。
        若 classDataOff != 0，则进一步解析 DexClassData (包含 Field/Method/Code)。
        """
        class_defs_size_int = int(self.DexHeader.class_defs_size or '0', 16)
        class_defs_off_int = int(self.DexHeader.class_defs_off or '0', 16)
        f = self.DexHeader.f

        for index in range(class_defs_size_int):
            # ---- 跳到当前 ClassDef 的起始位置 ----
            f.seek(class_defs_off_int + index*32, 0)

            # 1) 读取 classIdx (u4)
            classIdx_bytes = safe_read(f, 4)
            if classIdx_bytes is None:
                print(f"[init_DexClassDef] Not enough data for classIdx at index={index}, break.")
                break
            classIdx_hex = reverse_hex(binascii.b2a_hex(classIdx_bytes))
            classIdx = int(classIdx_hex, 16)

            # 2) 读取 accessFlags (u4)
            accessFlags_bytes = safe_read(f, 4)
            if accessFlags_bytes is None:
                print(f"[init_DexClassDef] Not enough data for accessFlags at index={index}, break.")
                break
            accessFlags_hex = reverse_hex(binascii.b2a_hex(accessFlags_bytes))
            accessFlags = int(accessFlags_hex, 16)

            # 3) 读取 superclassIdx (u4)
            superclassIdx_bytes = safe_read(f, 4)
            if superclassIdx_bytes is None:
                print(f"[init_DexClassDef] Not enough data for superclassIdx at index={index}, break.")
                break
            superclassIdx_hex = reverse_hex(binascii.b2a_hex(superclassIdx_bytes))
            superclassIdx = int(superclassIdx_hex, 16)

            # 4) 读取 interfaceOff (u4)
            interfaceOff_bytes = safe_read(f, 4)
            if interfaceOff_bytes is None:
                print(f"[init_DexClassDef] Not enough data for interfaceOff at index={index}, break.")
                break
            interfaceOff_hex = reverse_hex(binascii.b2a_hex(interfaceOff_bytes))
            interfaceOff = int(interfaceOff_hex, 16)

            # 5) 读取 sourceFieldIdx (u4)
            sourceFieldIdx_bytes = safe_read(f, 4)
            if sourceFieldIdx_bytes is None:
                print(f"[init_DexClassDef] Not enough data for sourceFieldIdx at index={index}, break.")
                break
            sourceFieldIdx_hex = reverse_hex(binascii.b2a_hex(sourceFieldIdx_bytes))
            sourceFieldIdx = int(sourceFieldIdx_hex, 16)

            # 6) 读取 annotationsOff (u4)
            annotationsOff_bytes = safe_read(f, 4)
            if annotationsOff_bytes is None:
                print(f"[init_DexClassDef] Not enough data for annotationsOff at index={index}, break.")
                break
            annotationsOff_hex = reverse_hex(binascii.b2a_hex(annotationsOff_bytes))
            annotationsOff = int(annotationsOff_hex, 16)

            # 7) 读取 classDataOff (u4)
            classDataOff_bytes = safe_read(f, 4)
            if classDataOff_bytes is None:
                print(f"[init_DexClassDef] Not enough data for classDataOff at index={index}, break.")
                break
            classDataOff_hex = reverse_hex(binascii.b2a_hex(classDataOff_bytes))
            classDataOff = int(classDataOff_hex, 16)

            # 8) 读取 staticValueOff (u4)
            staticValueOff_bytes = safe_read(f, 4)
            if staticValueOff_bytes is None:
                print(f"[init_DexClassDef] Not enough data for staticValueOff at index={index}, break.")
                break
            staticValueOff_hex = reverse_hex(binascii.b2a_hex(staticValueOff_bytes))
            staticValueOff = int(staticValueOff_hex, 16)

            # ---- 构造并存储 DexClassDef 对象 ----
            dexClassDefObj = DexClassDef()
            dexClassDefObj.classIdx = classIdx
            dexClassDefObj.accessFlags = accessFlags
            dexClassDefObj.superclassIdx = superclassIdx
            dexClassDefObj.interfaceOff = interfaceOff
            dexClassDefObj.sourceFieldIdx = sourceFieldIdx
            dexClassDefObj.annotationsOff = annotationsOff
            dexClassDefObj.classDataOff = classDataOff
            dexClassDefObj.staticValueOff = staticValueOff
            dexClassDefObj.offset = class_defs_off_int + index * 32
            dexClassDefObj.length = 32

            # 如果 classDataOff != 0，则进一步解析 DexClassData 结构
            if classDataOff != 0:
                # 解析 DexClassData
                f.seek(classDataOff, 0)
                dexClassDataHeader = []
                dexClassDataHeaderLength = 0

                # DexClassDataHeader 有4个 ULEB128：staticFieldsSize, instanceFieldsSize, directMethodsSize, virtualMethodsSize
                for i2 in range(4):
                    # 先读取1字节
                    c_byte = safe_read(f, 1)
                    if c_byte is None:
                        print(f"[init_DexClassDef] Not enough data reading DexClassDataHeader at index={index}, break.")
                        break
                    dexClassDataHeaderLength += 1
                    c_val = int(binascii.b2a_hex(c_byte), 16)
                    c_hex = binascii.b2a_hex(c_byte)

                    # 如果 >=0x80 说明后面还需继续读
                    while c_val > 0x7f:
                        c2 = safe_read(f, 1)
                        if c2 is None:
                            print("[init_DexClassDef] incomplete ULEB128 for DexClassDataHeader, break.")
                            break
                        dexClassDataHeaderLength += 1
                        c2_val = int(binascii.b2a_hex(c2), 16)
                        c_hex += binascii.b2a_hex(c2)
                        c_val = c2_val
                    dexClassDataHeader.append(c_hex)

                if len(dexClassDataHeader) < 4:
                    # 说明解析 header 中途失败
                    self.dexClassDefList.append(dexClassDefObj)
                    continue

                staticFieldsSize = self.readUnsignedLeb128(dexClassDataHeader[0])
                instanceFieldsSize = self.readUnsignedLeb128(dexClassDataHeader[1])
                directMethodsSize = self.readUnsignedLeb128(dexClassDataHeader[2])
                virtualMethodsSize = self.readUnsignedLeb128(dexClassDataHeader[3])

                dexClassDataHeaderObj = DexClassDataHeader()
                dexClassDataHeaderObj.staticFieldsSize = staticFieldsSize
                dexClassDataHeaderObj.instanceFieldsSize = instanceFieldsSize
                dexClassDataHeaderObj.directMethodsSize = directMethodsSize
                dexClassDataHeaderObj.virtualMethodsSize = virtualMethodsSize
                dexClassDataHeaderObj.offset = classDataOff
                dexClassDataHeaderObj.length = dexClassDataHeaderLength

                dexClassDefObj.header = dexClassDataHeaderObj

                # 继续解析 staticFields, instanceFields, directMethods, virtualMethods
                offset_in_classData = classDataOff + dexClassDataHeaderLength

                # ---- 1) staticFields ----
                last_offset = offset_in_classData
                for i2 in range(staticFieldsSize):
                    # 每个 DexField: 2 个 ULEB128 (fieldIdxDiff, accessFlags)
                    array_leb = []
                    length_field = 0
                    for j2 in range(2):
                        c_byte = safe_read(f, 1)
                        if c_byte is None:
                            print("[init_DexClassDef] Not enough data reading staticFields, break.")
                            break
                        length_field += 1
                        c_val = int(binascii.b2a_hex(c_byte), 16)
                        c_hex = binascii.b2a_hex(c_byte)
                        while c_val > 0x7f:
                            c2 = safe_read(f, 1)
                            if c2 is None:
                                print("[init_DexClassDef] incomplete ULEB128 in staticFields, break.")
                                break
                            length_field += 1
                            c2_val = int(binascii.b2a_hex(c2), 16)
                            c_hex += binascii.b2a_hex(c2)
                            c_val = c2_val
                        array_leb.append(c_hex)

                    if len(array_leb) < 2:
                        break

                    dexField = DexField()
                    dexField.fieldIdx = self.readUnsignedLeb128(array_leb[0])
                    dexField.accessFlags = self.readUnsignedLeb128(array_leb[1])
                    dexField.offset = last_offset
                    dexField.length = length_field

                    last_offset += length_field
                    dexClassDefObj.staticFields.append(dexField)

                # ---- 2) instanceFields ----
                for i2 in range(instanceFieldsSize):
                    array_leb = []
                    length_field = 0
                    for j2 in range(2):
                        c_byte = safe_read(f, 1)
                        if c_byte is None:
                            print("[init_DexClassDef] Not enough data reading instanceFields, break.")
                            break
                        length_field += 1
                        c_val = int(binascii.b2a_hex(c_byte), 16)
                        c_hex = binascii.b2a_hex(c_byte)
                        while c_val > 0x7f:
                            c2 = safe_read(f, 1)
                            if c2 is None:
                                print("[init_DexClassDef] incomplete ULEB128 in instanceFields, break.")
                                break
                            length_field += 1
                            c2_val = int(binascii.b2a_hex(c2), 16)
                            c_hex += binascii.b2a_hex(c2)
                            c_val = c2_val
                        array_leb.append(c_hex)

                    if len(array_leb) < 2:
                        break

                    dexField = DexField()
                    dexField.fieldIdx = self.readUnsignedLeb128(array_leb[0])
                    dexField.accessFlags = self.readUnsignedLeb128(array_leb[1])
                    dexField.offset = last_offset
                    dexField.length = length_field

                    last_offset += length_field
                    dexClassDefObj.instanceFields.append(dexField)

                # ---- 3) directMethods ----
                for i2 in range(directMethodsSize):
                    array_leb = []
                    length_method = 0
                    for j2 in range(3):
                        c_byte = safe_read(f, 1)
                        if c_byte is None:
                            print("[init_DexClassDef] Not enough data reading directMethods, break.")
                            break
                        length_method += 1
                        c_val = int(binascii.b2a_hex(c_byte), 16)
                        c_hex = binascii.b2a_hex(c_byte)
                        while c_val > 0x7f:
                            c2 = safe_read(f, 1)
                            if c2 is None:
                                print("[init_DexClassDef] incomplete ULEB128 in directMethods, break.")
                                break
                            length_method += 1
                            c2_val = int(binascii.b2a_hex(c2), 16)
                            c_hex += binascii.b2a_hex(c2)
                            c_val = c2_val
                        array_leb.append(c_hex)

                    if len(array_leb) < 3:
                        break

                    dexMethod = DexMethod()
                    dexMethod.methodIdx = self.readUnsignedLeb128(array_leb[0])
                    dexMethod.accessFlags = self.readUnsignedLeb128(array_leb[1])
                    dexMethod.codeOff = self.readUnsignedLeb128(array_leb[2])
                    dexMethod.offset = last_offset
                    dexMethod.length = length_method

                    last_offset += length_method
                    dexClassDefObj.directMethods.append(dexMethod)

                # ---- 4) virtualMethods ----
                for i2 in range(virtualMethodsSize):
                    array_leb = []
                    length_method = 0
                    for j2 in range(3):
                        c_byte = safe_read(f, 1)
                        if c_byte is None:
                            print("[init_DexClassDef] Not enough data reading virtualMethods, break.")
                            break
                        length_method += 1
                        c_val = int(binascii.b2a_hex(c_byte), 16)
                        c_hex = binascii.b2a_hex(c_byte)
                        while c_val > 0x7f:
                            c2 = safe_read(f, 1)
                            if c2 is None:
                                print("[init_DexClassDef] incomplete ULEB128 in virtualMethods, break.")
                                break
                            length_method += 1
                            c2_val = int(binascii.b2a_hex(c2), 16)
                            c_hex += binascii.b2a_hex(c2)
                            c_val = c2_val
                        array_leb.append(c_hex)

                    if len(array_leb) < 3:
                        break

                    dexMethod = DexMethod()
                    dexMethod.methodIdx = self.readUnsignedLeb128(array_leb[0])
                    dexMethod.accessFlags = self.readUnsignedLeb128(array_leb[1])
                    dexMethod.codeOff = self.readUnsignedLeb128(array_leb[2])
                    dexMethod.offset = last_offset
                    dexMethod.length = length_method

                    last_offset += length_method
                    dexClassDefObj.virtualMethods.append(dexMethod)

                # ---- 对每个 directMethod / virtualMethod，如果 codeOff != 0 则调用 parseDexCode ----
                for m in dexClassDefObj.directMethods:
                    if m.codeOff != 0:
                        m.dexCode = self.parseDexCode(m.codeOff)
                    else:
                        m.dexCode = None

                for m in dexClassDefObj.virtualMethods:
                    if m.codeOff != 0:
                        m.dexCode = self.parseDexCode(m.codeOff)
                    else:
                        m.dexCode = None

            # 最后将该 dexClassDefObj 放入列表
            self.dexClassDefList.append(dexClassDefObj)


    def print_DexClassDef(self):
        print('\n')
        print('[+] DexClassDef:')

        for index in range(len(self.dexClassDefList)):
            dexClassDefObj = self.dexClassDefList[index]
            print('    #%s~%s' % (hex(dexClassDefObj.offset), hex(dexClassDefObj.offset + dexClassDefObj.length)))
            print('    DexClassDef[%d]:\t' % index)
            print('    DexClassDef[%d]->classIdx\t= %s\t#%s' % (index, hex(dexClassDefObj.classIdx), self.getDexTypeId(dexClassDefObj.classIdx)))
            print('    DexClassDef[%d]->accessFlags\t= %s' % (index, hex(dexClassDefObj.accessFlags) ))
            print('    DexClassDef[%d]->superclassIdx\t= %s\t#%s' % (index, hex(dexClassDefObj.superclassIdx), self.getDexTypeId(dexClassDefObj.superclassIdx)))
            print('    DexClassDef[%d]->interfaceOff\t= %s' % (index, hex(dexClassDefObj.interfaceOff)))
            if dexClassDefObj.sourceFieldIdx == 0xffffffff:
                print('    DexClassDef[%d]->sourceFieldIdx\t= %s\t#UNKNOWN' % (index, hex(dexClassDefObj.sourceFieldIdx)))
            else:
                print('    DexClassDef[%d]->sourceFieldIdx\t= %s\t#%s' % (index, hex(dexClassDefObj.sourceFieldIdx), self.DexStringIdList[dexClassDefObj.sourceFieldIdx]))
            print('    DexClassDef[%d]->annotationsOff\t= %s' % (index, hex(dexClassDefObj.annotationsOff)))
            print('    DexClassDef[%d]->classDataOff\t= %s' % (index, hex(dexClassDefObj.classDataOff)))
            print('    DexClassDef[%d]->staticValueOff\t= %s' % (index, hex(dexClassDefObj.staticValueOff)))
            if dexClassDefObj.classDataOff == 0:
                continue
            print('    ------------------------------------------------------------------------')
            print('    # %s~%s' % (hex(dexClassDefObj.header.offset), hex(dexClassDefObj.header.offset + dexClassDefObj.header.length)))
            print('    DexClassDef[%d]->DexClassData->DexClassDataHeader->staticFieldsSize \t= %s' % (index, hex(dexClassDefObj.header.staticFieldsSize)))
            print('    DexClassDef[%d]->DexClassData->DexClassDataHeader->instanceFieldsSize \t= %s' % (index, hex(dexClassDefObj.header.instanceFieldsSize)))
            print('    DexClassDef[%d]->DexClassData->DexClassDataHeader->directMethodsSize \t= %s' % (index, hex(dexClassDefObj.header.directMethodsSize)))
            print('    DexClassDef[%d]->DexClassData->DexClassDataHeader->virtualMethodsSize \t= %s' % (index, hex(dexClassDefObj.header.virtualMethodsSize)))
            if len(dexClassDefObj.staticFields) > 0:
                print('    ------------------------------------------------------------------------')
                print('    # %s~%s' % (hex(dexClassDefObj.staticFields[0].offset), hex(dexClassDefObj.staticFields[-1].offset + dexClassDefObj.staticFields[-1].length)))
            if len(dexClassDefObj.staticFields) < 0 and len(dexClassDefObj.instanceFields) > 0:
                print('    ------------------------------------------------------------------------')
                print('    # %s~%s' % (hex(dexClassDefObj.instanceFields[0].offset), hex(
                    dexClassDefObj.instanceFields[-1].offset + dexClassDefObj.instanceFields[-1].length)))
            lastFieldIdx = 0
            for k in range(len(dexClassDefObj.staticFields)):
                currFieldIdx = lastFieldIdx + dexClassDefObj.staticFields[k].fieldIdx
                fieldName = self.getDexStringId(self.DexFieldIdList[currFieldIdx].nameIdx)
                lastFieldIdx = currFieldIdx
                print('    DexClassDef[%d]->DexClassData->staticFields[%d]\t= %s\t#%s' % (index, k, fieldName, dexClassDefObj.staticFields[k]))

            lastFieldIdx = 0
            for k in range(len(dexClassDefObj.instanceFields)):
                currFieldIdx = lastFieldIdx + dexClassDefObj.instanceFields[k].fieldIdx
                fieldName = self.getDexStringId(self.DexFieldIdList[currFieldIdx].nameIdx)
                lastFieldIdx = currFieldIdx
                print('    DexClassDef[%d]->DexClassData->instanceFields[%d]\t= %s\t#%s' % (index, k, fieldName, dexClassDefObj.instanceFields[k]))

            if len(dexClassDefObj.staticFields) + len(dexClassDefObj.instanceFields) > 0:
                print('    ------------------------------------------------------------------------')

            lastMethodIdx = 0
            for k in range(len(dexClassDefObj.directMethods)):
                currMethodIdx = lastMethodIdx + dexClassDefObj.directMethods[k].methodIdx
                dexMethodIdObj = self.DexMethodIdList[currMethodIdx]
                lastMethodIdx = currMethodIdx
                print('    # %s~%s' % (hex(dexClassDefObj.directMethods[k].offset), hex(dexClassDefObj.directMethods[k].offset + dexClassDefObj.directMethods[k].length)))
                print('    DexClassDef[%d]->DexClassData->directMethods[%d]\t= %s\t#%s' % (index, k, dexMethodIdObj.toString(self), dexClassDefObj.directMethods[k]))
                self.dumpDexCode(dexClassDefObj.directMethods[k])
                print('    ------------------------------------------------------------------------')

            lastMethodIdx = 0
            for k in range(len(dexClassDefObj.virtualMethods)):
                currMethodIdx = lastMethodIdx + dexClassDefObj.virtualMethods[k].methodIdx
                dexMethodIdObj = self.DexMethodIdList[currMethodIdx]
                lastMethodIdx = currMethodIdx
                print('    # %s~%s' % (hex(dexClassDefObj.virtualMethods[k].offset), hex(dexClassDefObj.virtualMethods[k].offset + dexClassDefObj.virtualMethods[k].length)))
                print('    DexClassDef[%d]->DexClassData->virtualMethods[%d]\t= %s\t#%s' % (index, k, dexMethodIdObj.toString(self), dexClassDefObj.virtualMethods[k]))
                self.dumpDexCode(dexClassDefObj.virtualMethods[k])
                print('    ------------------------------------------------------------------------')
            print('\n')

    def dumpDexCode(self, dexMethod):
        if dexMethod.dexCode == None:
            return
        print('    # %s~%s' % (hex(dexMethod.dexCode.offset), hex(dexMethod.dexCode.offset + dexMethod.dexCode.length)))
        print('    DexCode=%s' % dexMethod.dexCode)
        offset = 0
        insnsSize = dexMethod.dexCode.insnsSize * 4

        while offset < insnsSize:
            opcode = int(dexMethod.dexCode.insns[offset:offset + 2], 16)
            formatIns, _ = getOpCode(opcode)

            decodedInstruction = dexDecodeInstruction(self, dexMethod.dexCode, offset)

            smaliCode = decodedInstruction.smaliCode
            if smaliCode == None:
                continue

            insns = dexMethod.dexCode.insns[decodedInstruction.offset:decodedInstruction.offset + decodedInstruction.length]
            print('    \t%-16s|%04x: %s' % (insns, int(offset/4), smaliCode))
            offset += len(insns)

            if smaliCode == 'nop':
                break

    def parseDexCode(self, codeOff):
        f = self.DexHeader.f
        f.seek(codeOff, 0)

        # 1) registersSize (2字节)
        reg_bytes = safe_read(f, 2)
        if reg_bytes is None:
            print(f"[parseDexCode] Not enough data for registersSize at offset=0x{codeOff:x}")
            return None
        registersSize_hex = reverse_hex(binascii.b2a_hex(reg_bytes))
        registersSize = int(registersSize_hex, 16)

        # 2) insSize (2字节)
        ins_bytes = safe_read(f, 2)
        if ins_bytes is None:
            print("[parseDexCode] Not enough data for insSize.")
            return None
        insSize_hex = reverse_hex(binascii.b2a_hex(ins_bytes))
        insSize = int(insSize_hex, 16)

        # 3) outsSize (2字节)
        outs_bytes = safe_read(f, 2)
        if outs_bytes is None:
            print("[parseDexCode] Not enough data for outsSize.")
            return None
        outsSize_hex = reverse_hex(binascii.b2a_hex(outs_bytes))
        outsSize = int(outsSize_hex, 16)

        # 4) triesSize (2字节)
        tries_bytes = safe_read(f, 2)
        if tries_bytes is None:
            print("[parseDexCode] Not enough data for triesSize.")
            return None
        triesSize_hex = reverse_hex(binascii.b2a_hex(tries_bytes))
        triesSize = int(triesSize_hex, 16)

        # 5) debugInfoOff (4字节)
        debug_bytes = safe_read(f, 4)
        if debug_bytes is None:
            print("[parseDexCode] Not enough data for debugInfoOff.")
            return None
        debugInfoOff_hex = reverse_hex(binascii.b2a_hex(debug_bytes))
        debugInfoOff = int(debugInfoOff_hex, 16)

        # 6) insnsSize (4字节)
        insnsize_bytes = safe_read(f, 4)
        if insnsize_bytes is None:
            print("[parseDexCode] Not enough data for insnsSize.")
            return None
        insnsSize_hex = reverse_hex(binascii.b2a_hex(insnsize_bytes))
        insnsSize = int(insnsSize_hex, 16)

        # 7) 根据 insnsSize 读实际指令区
        if insnsSize == 0:
            insns_data_hex = ''
        else:
            read_len = insnsSize * 2
            insns_data = safe_read(f, read_len)
            if insns_data is None:
                print(f"[parseDexCode] Not enough data for insns (size={read_len} bytes).")
                return None
            insns_data_hex = binascii.b2a_hex(insns_data)

        dexCode = DexCode()
        dexCode.registersSize = registersSize
        dexCode.insSize = insSize
        dexCode.outsSize = outsSize
        dexCode.triesSize = triesSize
        dexCode.debugInfoOff = debugInfoOff
        dexCode.insnsSize = insnsSize
        dexCode.insns = insns_data_hex
        dexCode.offset = codeOff
        dexCode.length = 16 + (len(insns_data_hex)//2 if insns_data_hex else 0)

        return dexCode



    def readUnsignedLeb128(self, hex_value):
        byte_counts = int(len(hex_value)/2)

        #找出第一个不是0的byte位置
        index = 0
        for i in range(byte_counts):
            v1 = int(hex_value[i*2:i*2+2], 16)
            if v1 > 0:
                index = i
                break

        hex_value = hex_value[index*2:]
        byte_counts = int(len(hex_value)/2)

        result = 0
        for i in range(byte_counts):
            cur = int(hex_value[i*2:i*2+2], 16)
            if cur > 0x7f:
                result = result | ((cur & 0x7f) << (7*i))
            else:
                result = result | ((cur & 0x7f) << (7*i))
                break
        return result

class DexHeader(object):
    def __init__(self, ):
        super(DexHeader, self).__init__()
        self.f = None
        self.magic = None
        self.checksum = None
        self.signature = None
        self.file_size = None
        self.header_size = None
        self.endian_tag = None
        self.link_size = None
        self.link_off = None
        self.map_off = None
        self.string_ids_size = None
        self.string_ids_off = None
        self.type_ids_size = None
        self.type_ids_off = None
        self.proto_ids_size = None
        self.proto_ids_off = None
        self.field_ids_size = None
        self.field_ids_off = None
        self.method_ids_size = None
        self.method_ids_off = None
        self.class_defs_size = None
        self.class_defs_off = None
        self.data_size = None
        self.data_off = None


class DexProtoId(object):
    def __init__(self, ):
        super(DexProtoId, self).__init__()
        self.shortyIdx = None
        self.returnTypeIdx = None
        self.parameterOff = None
        self.dexTypeList = None

        # Address index
        self.offset = None
        self.length = 0

    def toString(self, dexFile):
        if self.dexTypeList:
            return '%s%s' % (self.dexTypeList.toString(dexFile),  dexFile.getDexTypeId(self.returnTypeIdx))
        else:
            return '()%s' % dexFile.getDexTypeId(self.returnTypeIdx)

class DexTypeList(object):
    def __init__(self, ):
        super(DexTypeList, self).__init__()
        self.size = None
        self.list = []

    def toString(self, dexFile):
        parametersStr = ''
        if self.size:
            for idx in self.list:
                parametersStr += dexFile.getDexTypeId(idx) + ','
        return '(%s)' % parametersStr

class DexMethodId(object):
    def __init__(self, ):
        super(DexMethodId, self).__init__()
        self.classIdx = None
        self.protoIdx = None
        self.nameIdx = None

        # Address index
        self.offset = None
        self.length = 0

    def toString(self, dexFile):
        if (self.classIdx != None) and (self.protoIdx != None) and (self.nameIdx != None):
            return '%s.%s:%s' % (dexFile.getDexTypeId(self.classIdx),
                                 dexFile.getDexStringId(self.nameIdx),
                                 dexFile.DexProtoIdList[self.protoIdx].toString(dexFile))
        else:
            return None

    def toApi(self, dexFile):
        if (self.classIdx != None) and (self.protoIdx != None) and (self.nameIdx != None):
            return '%s->%s' % (dexFile.getDexTypeId(self.classIdx),
                                 dexFile.getDexStringId(self.nameIdx))
        else:
            return None

class DexFieldId(object):
    def __init__(self, ):
        super(DexFieldId, self).__init__()
        self.classIdx = None
        self.typeIdx = None
        self.nameIdx = None

        # Address index
        self.offset = None
        self.length = 0

    def toString(self, dexFile):
        if (self.classIdx != None) and (self.typeIdx != None) and (self.nameIdx != None):
            return '%s.%s:%s' % (dexFile.getDexTypeId(self.classIdx),
                                 dexFile.getDexStringId(self.nameIdx),
                                 dexFile.getDexTypeId(self.typeIdx))
        else:
            return None

class DexClassDef(object):
    def __init__(self,):
        super(DexClassDef, self).__init__()
        self.classIdx = None
        self.accessFlags = None
        self.superclassIdx = None
        self.interfaceOff = None
        self.sourceFieldIdx = None
        self.annotationsOff = None
        self.classDataOff = None
        self.staticValueOff = None

        self.header = None
        self.staticFields = []
        self.instanceFields = []
        self.directMethods = []
        self.virtualMethods = []

        # Address index
        self.offset = None
        self.length = 0

class DexClassDataHeader(object):
    """docstring for ClassName"""
    def __init__(self):
        super(DexClassDataHeader, self).__init__()
        self.staticFieldsSize = None
        self.instanceFieldsSize = None
        self.directMethodsSize = None
        self.virtualMethodsSize = None

        # Address index
        self.offset = None
        self.length = 0

class DexField(object):
    """docstring for DexField"""
    def __init__(self):
        super(DexField, self).__init__()
        self.fieldIdx = None
        self.accessFlags = None

        # Address index
        self.offset = None
        self.length = 0

    def __str__(self):
        return '[fieldIdx = %s, accessFlags = %s]' % (hex(self.fieldIdx), hex(self.accessFlags))


class DexMethod(object):
    """docstring for DexMethod"""
    def __init__(self):
        super(DexMethod, self).__init__()
        self.methodIdx = None
        self.accessFlags = None
        self.codeOff = None

        # Address index
        self.offset = None
        self.length = 0

        self.dexCode = DexCode()

    def __str__(self):
        return '[methodIdx = %s, accessFlags = %s, codeOff = %s]' % (hex(self.methodIdx), hex(self.accessFlags), hex(self.codeOff))

class DexCode(object):
    """docstring for DexCode"""
    def __init__(self):
        super(DexCode, self).__init__()
        self.registersSize = None
        self.insSize = None
        self.outsSize = None
        self.triesSize = None
        self.debugInfoOff = None
        self.insnsSize = None
        self.insns = None

        # Address index
        self.offset = None
        self.length = 0

    def __str__(self):
        return '[registersSize = %s, insSize = %s, outsSize = %s, triesSize = %s, debugInfoOff = %s, insnsSize = %s, insns = %s]' % \
                (self.registersSize, self.insSize, self.outsSize, self.triesSize, hex(self.debugInfoOff), self.insnsSize, self.insns)


def main():
    dex = DexFile(sys.argv[1])
    dex.print_header()
    dex.print_DexMapList()
    dex.print_DexStringId()
    dex.print_DexTypeId()
    dex.print_DexProtoId()
    dex.print_DexFieldId()
    dex.print_DexMethodId()
    dex.print_DexClassDef()

if __name__ == '__main__':
    main()
