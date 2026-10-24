# SPDX-License-Identifier: Apache-2.0
# X6 adaptation; upstream protocol credit is recorded in ATTRIBUTION.md.
import base64
import hashlib
import json
from pathlib import Path
import re
import socket
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import x6_root as x


def field(number, value):
    return x.varint((number << 3) | 2) + x.varint(len(value)) + value


def identity_reply(serial=b'TEST_ONLY', version=b'v0.8.825', model=b'Insta360 X6'):
    return field(2, field(15, serial) + field(30, version) + field(48, model))


class Tests(unittest.TestCase):
    def test_reference_frames(self):
        wire = bytes.fromhex('55434432010c04010f000000c800020100008000000803080208011d33f73d')
        heartbeat = bytes.fromhex('55434432010c050200000000f67b418a')
        result, rest = x.frames(wire + heartbeat)
        self.assertEqual(len(result), 2); self.assertEqual(rest, b'')
        self.assertEqual(x.frame(4, wire[12:-4], 1), wire)
        self.assertEqual(x.frame(5, b'', 2), heartbeat)

    def test_partial_and_corrupt_frame(self):
        wire = x.frame(4, b'example', 1)
        for i in range(len(wire)):
            self.assertEqual(x.frames(wire[:i]), ([], wire[:i]))
        broken = bytearray(wire); broken[12] ^= 1
        with self.assertRaises(ValueError): x.frames(bytes(broken))
        with self.assertRaises(ValueError): x.frames(b'NOPE' + wire[4:])
        oversized = bytearray(wire); struct.pack_into('<I', oversized, 8, x.MAX_FRAME + 1)
        with self.assertRaises(ValueError): x.frames(bytes(oversized))

    def test_wire_fields(self):
        self.assertEqual(x.fields(field(30, b'v0.8.825'))[30], [b'v0.8.825'])
        self.assertEqual(x.fields(b'\x08\x00'), {1: [0]})
        for bad in [b'\0', b'\x0a\xff', b'\x0a\x03x', b'\x08'+b'\xff'*10, b'\x0b']:
            with self.assertRaises(ValueError): x.fields(bad)
        with self.assertRaises(ValueError): x.one({1: [0, 1]}, 1)

    def test_identity(self):
        s = x.Session.__new__(x.Session)
        s.query = lambda method, body: identity_reply()
        self.assertEqual(s.identity(), ('TEST_ONLY', 'v0.8.825'))
        saved = {'serial_sha256': hashlib.sha256(b'TEST_ONLY').hexdigest()}
        self.assertEqual(x.identify(s, saved), 'v0.8.825')
        with self.assertRaises(RuntimeError): x.identify(s, {'serial_sha256': '0'*64})

    def test_wrong_firmware_and_model(self):
        s = x.Session.__new__(x.Session)
        for v,m in [(b'1.2.36',b'Insta360 X6'),(b'v0.8.825',b'Other'),(b'',b'X6'),(b'vv0.8.825',b'X6')]:
            s.query = lambda method, body: identity_reply(version=v, model=m)
            with self.assertRaises(RuntimeError): s.identity()
        s.query = lambda method, body: field(2, b'\x78\x01')
        with self.assertRaises(ValueError): s.identity()

    def test_authorization_and_encoding(self):
        s = x.Session.__new__(x.Session)
        seen = []
        def q(m,b): seen.append((m,b)); return b'\x08\x00'
        s.query = q
        self.assertTrue(s.authorized('client'))
        self.assertEqual(seen, [(39,b'\x0a\x06client\x10\x01')])
        s.query = lambda m,b: b'\x08\x02'
        self.assertFalse(s.authorized('client'))
        s.query = lambda m,b: b'\x22\x04test' # proto3 zero omitted
        self.assertTrue(s.authorized('client'))
        s.query = lambda m,b: b''
        with self.assertRaises(RuntimeError): s.authorized('client')
        for invalid in [b'\xf8\x07\x00', b'\x22\x00', b'\x0a\x01x', b'\x08\x00\x08\x02']:
            s.query = lambda m,b: invalid
            with self.assertRaises(ValueError): s.authorized('client')

    def test_gui_payload_exact_bytes(self):
        command = "printf '%s\\n' 'spaces and quotes'"
        data = x.gui_request(command, '192.168.42.2', 45124)
        self.assertTrue(data.startswith(b'DeveloperExecuteCommand_Action {"DeveloperExecuteCommand":%s} '))
        encoded = data.split(b'echo${IFS}',1)[1].split(b'|',1)[0]
        self.assertEqual(base64.b64decode(encoded).decode(), command)
        self.assertTrue(data.endswith(b'${IFS}45124\n'))
        for host in ['127.0.0.1', '8.8.8.8', '192.168.42.1', '192.168.42.2;id']:
            with self.assertRaises(ValueError): x.gui_request('id',host,45124)
        with self.assertRaises(ValueError): x.gui_request('x'*1000,'192.168.42.2',45124)

    def test_root_requires_uid_and_fresh_marker(self):
        def reply(s,c):
            nonce=re.search(r'[0-9a-f]{24}',c)[0]
            return f'uid=0(root) gid=0(root)\n{nonce}\n'.encode()
        with patch.object(x,'execute',reply),patch('builtins.print'): x.root_check(None)
        for invalid in [b'STATUS:0 / Pack success', b'uid=2000(shell)', b'uid=0(root)\nold-marker\n']:
            with patch.object(x,'execute',return_value=invalid), self.assertRaises(RuntimeError): x.root_check(None)

    def test_state_is_local_and_identity_bound(self):
        with tempfile.TemporaryDirectory() as d, patch.object(x,'STATE',Path(d)/'state'):
            state={'version':'0.8.825','serial_sha256':hashlib.sha256(b'TEST_ONLY').hexdigest(),'client':'x6-owner-'+'1'*24}
            x.STATE.write_text(json.dumps(state)); self.assertEqual(x.read_state(),state)
            state['version']='1.2.36'; x.STATE.write_text(json.dumps(state))
            with self.assertRaises(ValueError): x.read_state()
            for invalid in [[], None, {'version':'0.8.825','serial_sha256':123,'client':None}]:
                x.STATE.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError): x.read_state()

    def test_completion_shell_and_exit_status(self):
        marker='X6_DONE_'+'1'*24
        for command,expected in [("printf '%s' 'spaces: 你好'",'spaces: 你好'.encode()),('printf hello; exit 0',b'hello')]:
            run=subprocess.run(['/bin/sh','-c',x.completed_command(command,marker)],capture_output=True,check=True)
            self.assertEqual(x.completed_output(run.stdout,marker),expected)
        run=subprocess.run(['/bin/sh','-c',x.completed_command('exit 7',marker)],capture_output=True,check=True)
        with self.assertRaisesRegex(RuntimeError,'status 7'): x.completed_output(run.stdout,marker)

    def test_completion_requires_exact_final_nonce(self):
        marker='X6_DONE_'+'1'*24
        tail=f'\n{marker}:0\n'.encode()
        for bad in [b'partial',tail[:-1],tail+b'extra',tail.replace(b'1',b'2'),tail.replace(b':0',b':999')]:
            with self.assertRaisesRegex(RuntimeError,'completion marker'): x.completed_output(bad,marker)
        self.assertEqual(x.completed_output(b'hello\n'+tail,marker),b'hello\n')

    def test_output_limit_with_completion_overhead(self):
        marker='X6_DONE_'+'1'*24;tail=f'\n{marker}:0\n'.encode()
        self.assertEqual(len(x.completed_output(b'x'*65536+tail,marker)),65536)
        with self.assertRaisesRegex(RuntimeError,'Output limit'): x.completed_output(b'x'*65537+tail,marker)

    def test_readme_command_fits_with_wrapper(self):
        readme=Path(__file__).with_name('README.md').read_text(encoding='utf-8')
        command=re.search(r'(?m)^p=\$\(/bin/busybox mktemp .*\ntrap .*\nprintf .*\n',readme)[0]
        data=x.gui_request(x.completed_command(command,'X6_DONE_'+'1'*24),'192.168.42.2',45124)
        self.assertLess(len(data),1000)

    def test_bilingual_examples_match(self):
        examples=[]
        for name in ['README.md','README.en.md']:
            text=Path(__file__).with_name(name).read_text(encoding='utf-8')
            examples.append(re.findall(r'```(?:sh|text)\n(.*?)\n```',text,re.S))
        self.assertTrue(examples[0])
        self.assertEqual(examples[0],examples[1])

    def test_correlated_reply(self):
        s=x.Session.__new__(x.Session);s.mid=0
        sent=[];s.send=lambda k,b:sent.append((k,b))
        s.tick=lambda timeout:[(4,struct.pack('<HBIH',200,2,99,0)+b'other'),(4,struct.pack('<HBIH',200,2,1,0)+b'ok')]
        self.assertEqual(s.query(8,b'options'),b'ok')
        self.assertEqual(sent,[(4,struct.pack('<HBIH',8,2,0x80000001,0)+b'options')])
        s.tick=lambda timeout:[(4,struct.pack('<HBIH',400,2,s.mid,0))]
        with self.assertRaises(RuntimeError):s.query(8)


if __name__ == '__main__':
    unittest.main()
