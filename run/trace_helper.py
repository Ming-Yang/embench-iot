'''Examples:
To convert a qemu-trace "./lisa_perf_func/debug.log" into a more usefull trace "./golden_trace.txt"
Assuming file "godson_test.s" is under directory "./lisa_perf_func":
    cat ./lisa_perf_func/debug.log | python trace_helper.py convert -p ./lisa_perf_func > ./golden_trace.txt

To get dynamical instruction frequencies of a qemu-trace "./lisa_perf_func/debug.log":
Also, Assuming file "godson_test.s" is under directory "./lisa_perf_func":
    cat ./lisa_perf_func/debug.log | python trace_helper.py freq -p ./lisa_perf_func

To get dynamical instruction frequencies of a PC-only qemu-trace "./embench_int/crc32/crc32.log":
Assuming file "godson_test.s" is under directory "./embench_int/crc32":
    cat ./embench_int/crc32/crc32.log | python trace_helper.py freq -p ./embench_int/crc32 --no_regfile

To diff two files at "./lisa_perf_func/godson_test.s" and "lisa_inst_func/godson_test.s".
Assuming their last instrution is at 0x1d3a00 0x267600 respectly:
    python trace_helper.py diff -p lisa_perf_func --until 1d3a00 --subtract lisa_inst_func/godson_test.s --until 267600
    
To create an "axi_ram.dat" file with "godson_test.s" under directory "./embench_int/crc32"
    python trace_helper.py dump -p ./embench_int/crc32 --align 3 
    
To create all "axi_ram.dat" file with "godson_test.s" under subdirectories of directory "./embench_int"
    python trace_helper.py dumpdats -p ./embench_int --align 3
'''
import os
import sys
from functools import reduce
class Status:
    sample = '''pc=0x*
GPR00: r0 * ra * fp * sp *
GPR04: a0 * a1 * a2 * a3 *
GPR08: a4 * a5 * a6 * a7 *
GPR12: t0 * t1 * t2 * t3 *
GPR16: t4 * t5 * t6 * t7 *
GPR20: t8 * gp * fp * s0 *
GPR24: s1 * s2 * s3 * s4 *
GPR28: s5 * s6 * s7 * s8 *
    CSR_EPC 0x* CSR_RFEPC 0x*
    CSR_CRMD 0x* CSR_PRMD 0x*
    CSR_EXCONFIG 0x* CSR_EXSTATUS 0x*'''
    sample_lines = sample.split('\n')
    sample_words = [line.split('*') for line in sample_lines]
    length = len(sample_words)
    nwords = [len(line) for line in sample_words]
    def __init__(self,stream,rf=True):
        lines = [next(stream) for i in range(self.length)]
        self.valid = True if lines[-1] else False
        if not self.valid:return
        base = len(self.sample_words[0][0])
        self.pc = int(lines[0][base:base+16],16)
        if not rf:return
        self.rf = []
        for i in range(1,len(self.sample_words)):
            base = 0
            for j in range(len(self.sample_words[i])-1):
                word = self.sample_words[i][j]
                base+=len(word)
                val = lines[i][base:base+16]
                base+= 16
                val = int(val,16)
                self.rf.append(val)
            if len(self.rf)>=32:break
    def diff(self,prev):
        return (prev.pc,{i:self.rf[i] for i in range(len(self.rf)) if self.rf[i]!=prev.rf[i]})
def get_diff(trace):
    prev = next(trace)
    cur  = next(trace)
    for i in range(32):
        print('%016x'%prev.rf[i])
    for status in trace:
        pc,diff = cur.diff(prev)
        if len(diff)>1:
            yield pc,{1:diff[1]}
            del diff[1]
        if len(diff)>0:
            yield pc,diff
        prev = cur
        cur  = status
def get_change(trace):
    diffs = get_diff(trace)
    prev_pc,prev_diff = next(diffs)
    for cur_pc,cur_diff in diffs:
        if len(prev_diff)==1:
            for i,v in prev_diff.items():
                if i not in cur_diff:
                    yield (prev_pc,prev_diff)
        elif prev_pc!=cur_pc:yield (prev_pc,prev_diff)
        else:
            for i,v in prev_diff.items():
                if i not in cur_diff:
                    raise ValueError('Found invalid format for trace.')
        prev_pc,prev_diff = cur_pc,cur_diff
def get_trace_entry(trace,branchs,uncared):
    for pc,diff in get_change(trace):
        if len(diff)>1:raise ValueError()
        if pc in branchs:
            if 1 in diff and pc==diff[1]:
                yield '1 %016x 1 01 %016x'%(pc,pc+4)
            else:
                yield '0 %016x 1 '%pc + ' '.join('%02x %016x'%(i,v) for i,v in diff.items())
        else:
            care = 0 if pc in uncared else 1
            yield '%d %016x 1 '%(care,pc) + ' '.join('%02x %016x'%(i,v) for i,v in diff.items())
def get_status(stream,args):
    while True:
        status = Status(stream,rf=args.regfile)
        if not status.valid:break
        yield status
def get_stream_stdin():
    for line in sys.stdin:
        yield line
    while True:
        yield None
def get_stream_path(fname):
    with open(fname,'rt') as f:
        line = f.readline()
        while line:
            yield line
            line = f.readline()
    while True:
        yield None
def outout_trace(args):
    branchs = get_branch(os.path.join(args.prefix,args.source))
    uncared = set(int(pc,16) for pc in args.ignore)
    stream = get_stream_stdin() if args.trace == '' else get_stream_path(os.path.join(args.prefix,args.trace))
    trace = get_status(stream,args=args)
    for entry in get_trace_entry(trace,branchs,uncared):
        print(entry)
def get_inst_freq(args):
    inst_map = get_inst_map(os.path.join(args.prefix,args.source))
    stream = get_stream_stdin() if args.trace == '' else get_stream_path(os.path.join(args.prefix,args.trace))
    trace = get_status(stream,args=args)
    freq = {}
    for status in trace:
        name = inst_map[status.pc]
        freq[name] = freq.get(name,0)+1
    return freq
def output_inst_freq(args):
    freq = get_inst_freq(args)
    count = sum(n for name,n in freq.items())
    info = [(name,n/count) for name,n in freq.items()]
    info = sorted(info,key=lambda a:a[1],reverse=True)
    print('Dynamical Instruction Count:',count)
    print('Instrution Frequencies:')
    a = 0
    for name,f in info:
        print('%s\t%.2f'%(name,100*f))
        a += f
def get_inst(src):
    with open(src,'rt') as f:
        for line in f.readlines():
            if not line.startswith('  '):continue
            if not line[ 8:10] == ':\t':continue
            if not line[18:20] == ' \t':continue
            if not line[ 2: 8].isalnum():continue
            loc = int(line[ 2: 8],16)
            if loc>=0x400000:continue
            if not line[10:18].isalnum():continue
            inst = line[20:].split('\t')[0]
            for part in inst.split('.'):
                if not part.isidentifier():break
            else:
                yield inst,loc
def get_inst_set(src,tail=None):
    insts = set()
    for inst,loc in get_inst(src):
        if not tail is None and loc > tail:break
        insts.add(inst)
    return insts
def get_inst_map(src,tail=None):
    insts = {}
    for inst,loc in get_inst(src):
        if not tail is None and loc > tail:break
        insts[loc] = inst
    return insts
def get_branch(src,tail=None):
    branch = set()
    for inst,loc in get_inst(src):
        if not tail is None and loc > tail:break
        if inst not in {'bl','b','jirl','bne','beq','bge','blt','bgeu','bltu','beqz','bnez'}:continue
        branch.add(loc)
    return branch
def get_inst_loc(src,tail=None):
    stat = {}
    for inst,loc in get_inst(src):
        if not tail is None and loc > tail:break
        stat[inst] = stat.get(inst,[])+[loc]
    return stat
def inst_set_diff(args):
    inst_set = get_inst_set(os.path.join(args.prefix,args.source),tail=int(args.until[0],16))
    for i in range(len(args.subtract)):
        inst_set = inst_set - get_inst_set(args.subtract[i],tail=int(args.until[i+1],16))
        if len(inst_set) == 0:break
    if len(args.subtract) > 0:
        if len(inst_set)>0:
            print('%d insts uncovered, they are:'%len(inst_set))
            inst_loc = get_inst_loc(os.path.join(args.prefix,args.source),tail=int(args.until[0],16))
            for name in inst_set:
                print(name,'(%d times), first occurs at %06x'%(len(inst_loc[name]),inst_loc[name][0]))
        else:
            print('Every inst is covered.')
    else:
        print('Totally %d insts:'%len(inst_set))
        for name in inst_set:
            print(name)
class Section:
    @property
    def stop(self):return self.start + (len(self.datas)<<2)
    def __init__(self,name):
        self.name = name
        self.start = None
        self.datas = []
    def fill_to(self,addr):
        while addr > self.stop:
            self.datas.append(0)
    def append(self,addr,data):
        self.fill_to(addr)
        self.datas.append(data)
    def set_ptr(self,addr):
        if self.start is None:
            assert (addr&0x3)==0
            self.start = addr
        else:
            self.fill_to(addr)
    def merge(self,other):
        assert self.stop <= other.start
        self.fill_to(other.start)
        self.datas.extend(other.datas)
    def format_dat(self,align):
        lines = ['@%x'%(self.start>>align)]
        datas = ['%08x'%data for data in self.datas]
        start = self.start&((1<<align) - 1)
        for i in range(0,start,4):datas.insert(0,'00000000')
        if align > 2:
            step = 1<<(align-2)
            for i in range(0,len(datas),step):
                data = ''
                for j in range(i,min(len(datas),i+step)):
                    data = datas[j] + data
                lines.append(data)
            if len(lines[-1]) < (2<<align):
                lines[-1]+='0'*(2<<align)
        elif align == 2:
            lines.extend(datas)
        else:
            for data in datas:
                lines.extend([data[i:i+(2<<align)] for i in range(0,8,2<<align)])
        return lines
def get_data_sections(src):
    segs= {}
    cur = None
    with open(src,'rt') as f:
        for line in f.readlines():
            if line.startswith('Disassembly of section .'):
                name = line[len('Disassembly of section .'):].split(':')[0]
                if name in segs:
                    cur = segs[name]
                else:
                    cur = Section(name)
                    segs[name] = cur
            elif line == '\n':continue
            elif cur is None:continue
            elif line == '	...\n':continue
            elif line.startswith('  '):
                parts = line.split('\t')
                addr = int(parts[0][:-1].strip(),16)
                data = parts[1].strip()
                if data.isalnum():
                    cur.append(addr,int(data,16))
                else:
                    cur.set_ptr(addr)
            elif line.startswith('00000000'):
                cur.set_ptr(int(line[:16],16))
            else:
                continue
    segs= [seg for name,seg in segs.items()]
    segs= sorted(segs,key=lambda a:a.start)
    mseg= []
    for seg in segs:
        if len(mseg)<=0:mseg.append(seg)
        else:
            if mseg[-1].stop + 128 > seg.start:
                mseg[-1].merge(seg)
            else:
                mseg.append(seg)
    return mseg
def output_ram_dat(segs,f,args):
    align = int(args.align)
    rambase = int(args.rambase)
    ramsize = int(args.ramsize)
    ramstop = rambase + (1<<ramsize)
    for seg in segs:
        # Make sure that the section fits into the ram
        if rambase>seg.stop:continue
        if ramstop<seg.start:continue
        if rambase>seg.start:
            seg.datas = seg.datas[rambase - seg.start:]
            seg.start = rambase
        if ramstop<seg.stop:
            seg.datas = seg.datas[:ramstop-seg.stop]
        seg.datas.extend([0]*16)
        for line in seg.format_dat(align):
            print(line,file=f)
def dump_select_output(target,segs,args):
    if args.ramname=='stdout':
        output_ram_dat(segs,sys.stdout,args)
    else:
        with open(target,'wt') as f:
            output_ram_dat(segs,f,args)
def dump_ram_dat(args):
    source = os.path.join(args.prefix,args.source)
    target = os.path.join(args.prefix,args.ramname)
    segs = get_data_sections(source)
    dump_select_output(target,segs,args)
def get_dirs(path,selected):
    for root, dirs, files in os.walk(path):
        if root != path:break
        for d in dirs:
            for r in get_dirs(os.path.join(root,d),selected):
                yield os.path.join(d,r)
        if len([f for f in files if selected(f)]) >0:yield '.'
def dump_ram_dats(args):
    for soft in get_dirs(args.prefix,lambda x:x == args.source):
        source = os.path.join(args.prefix,soft,args.source)
        target = os.path.join(args.prefix,soft,args.ramname)
        print('Dumping',source,file=sys.stderr)
        segs = get_data_sections(source)
        dump_select_output(target,segs,args)
        
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("action",choices=['convert','freq','diff','dump','dumpall'],default='convert')
    parser.add_argument("--no_regfile",action='store_false',dest='regfile')
    parser.add_argument("-p","--prefix",help='The prefix of path',default='./')
    parser.add_argument("-t","--trace",help='Specifying the dumped trace',default='')
    parser.add_argument("-s","--source",help='Specifying the dumped source',default='godson_test.s')
    parser.add_argument("--subtract",help='',action='append',default=[])
    parser.add_argument("--until",help='',action='append',default=[])
    parser.add_argument("-i","--ignore",help="The PC addresses to ignore",action='append',default=[])
    parser.add_argument("-a","--align",default='2')
    parser.add_argument("--ramname",help='Name of ram file',default='axi_ram.dat')
    parser.add_argument("--rambase",help='Base address of ram to generate',default='0')
    parser.add_argument("--ramsize",help='Maximum size of ram to generate',default='28')
    args = parser.parse_args()
    if args.action == 'convert':
        outout_trace(args)
    elif args.action == 'freq':
        output_inst_freq(args)
    elif args.action == 'diff':
        inst_set_diff(args)
    elif args.action == 'dump':
        dump_ram_dat(args)
    elif args.action == 'dumpall':
        dump_ram_dats(args)
