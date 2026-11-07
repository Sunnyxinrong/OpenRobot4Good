"""Minimal read-only Apache Parquet footer inspector (Thrift Compact Protocol).

This inspects structural metadata only; it does NOT decode data pages or prove
that the full training loader works. No third-party dependency is required.
Protocol references: parquet.apache.org/docs/file-format/metadata/ and
github.com/apache/thrift/blob/master/doc/specs/thrift-compact-protocol.md.
"""
from pathlib import Path
import struct

class CompactReader:
    def __init__(self,data):self.data=data;self.pos=0
    def take(self,n):
        if n<0 or self.pos+n>len(self.data):raise ValueError('Truncated Thrift field')
        v=self.data[self.pos:self.pos+n];self.pos+=n;return v
    def byte(self):return self.take(1)[0]
    def varint(self):
        v=0
        for s in range(0,70,7):
            b=self.byte();v|=(b&127)<<s
            if b<128:return v
        raise ValueError('Oversized varint')
    def integer(self):
        n=self.varint();return (n>>1)^-(n&1)
    def value(self,t,depth=0):
        if depth>64:raise ValueError('Excessive metadata nesting')
        if t==1:return True
        if t==2:return False
        if t==3:return struct.unpack('b',self.take(1))[0]
        if t in (4,5,6):return self.integer()
        if t==7:return struct.unpack('<d',self.take(8))[0]
        if t==8:return self.take(self.varint()).decode('utf-8',errors='replace')
        if t in (9,10):
            h=self.byte();size=h>>4;et=h&15
            if size==15:size=self.varint()
            if size>1_000_000:raise ValueError('Oversized metadata list')
            return [self.value(et,depth+1) for _ in range(size)]
        if t==11:
            size=self.varint()
            if not size:return []
            h=self.byte();return [(self.value(h>>4,depth+1),self.value(h&15,depth+1)) for _ in range(size)]
        if t==12:return self.structure(depth+1)
        raise ValueError(f'Unsupported compact type {t}')
    def structure(self,depth=0):
        result={};last=0
        while True:
            h=self.byte()
            if not h:return result
            delta=h>>4;t=h&15
            fid=last+delta if delta else self.integer()
            result[fid]=self.value(t,depth+1);last=fid

def inspect(path):
    data=Path(path).read_bytes()
    if len(data)<12 or data[:4]!=b'PAR1' or data[-4:]!=b'PAR1':raise ValueError('Invalid Parquet magic')
    n=struct.unpack('<I',data[-8:-4])[0]
    if n>len(data)-12:raise ValueError('Invalid footer length')
    reader=CompactReader(data[-8-n:-8]);m=reader.structure()
    return {'rows':m[3],'row_groups':len(m[4]),'created_by':m.get(6),
            'schema':[{'name':x.get(4),'physical_type':x.get(1),'children':x.get(5),'repetition':x.get(3)} for x in m[2]],
            'column_paths':[c[3][3] for c in m[4][0][1]] if m[4] else [],
            'scope':'Parquet footer/schema only; data pages and videos not decoded'}

if __name__=='__main__':
    import sys,json
    print(json.dumps(inspect(sys.argv[1]),indent=2))
