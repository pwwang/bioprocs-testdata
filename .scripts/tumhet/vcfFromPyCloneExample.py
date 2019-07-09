#!/usr/bin/env python
import sys
import random
import tempfile
from pathlib import Path
from remotedata import GithubRemoteData, CONFIG
from pyppl import PyPPL
from bioprocs.vcf import pVcfSplit
from bioprocs.utils.tsvio2 import TsvReader

TMPDIR = tempfile.gettempdir()
CONFIG = CONFIG.copy()
CONFIG.update(dict(
	source   = 'github',
	cachedir = TMPDIR,
	repos    = 'aroth85/pyclone',
))
RDATA = GithubRemoteData(CONFIG)

VCFHEADER = '\n'.join([
	'##fileformat=VCFv4.0',
	'##FILTER=<ID=PASS,Description="All filters passed">',
	'##reference=human_b36_both.fasta',
	'##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
	'##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Read Depth">',
	'##FORMAT=<ID=AD,Number=2,Type=Integer,Description="Number of each alleles">',
	'##FORMAT=<ID=CN,Number=1,Type=Integer,Description="Copy number of the major allele">',
	'##contig=<ID=chr1>',
	'##contig=<ID=chr2>',
	'##contig=<ID=chr3>',
	'##contig=<ID=chr4>',
	'##contig=<ID=chr5>',
	'##contig=<ID=chr6>',
	'##contig=<ID=chr7>',
	'##contig=<ID=chr8>',
	'##contig=<ID=chr9>',
	'##contig=<ID=chr10>',
	'##contig=<ID=chr11>',
	'##contig=<ID=chr12>',
	'##contig=<ID=chr13>',
	'##contig=<ID=chr14>',
	'##contig=<ID=chr15>',
	'##contig=<ID=chr16>',
	'##contig=<ID=chr17>',
	'##contig=<ID=chr18>',
	'##contig=<ID=chr19>',
	'##contig=<ID=chr20>',
	'##contig=<ID=chr21>',
	'##contig=<ID=chr22>',
	'##contig=<ID=chrX>',
	'##contig=<ID=chrY>',
	'#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{samples}'])

def convert2vcf(path):
	#mutation_id	ref_counts	var_counts	normal_cn	minor_cn	major_cn	variant_case	variant_freq	genotype
	#NA12156:BB:chr1:70820008	2538	91	2	0	2	NA12156	0.034613921643210345	BB
	reader  = TsvReader(RDATA.get(path))
	samples = sorted(list(set(reader.dump(6))))
	outfile = Path(TMPDIR) / (Path(path).stem + '.vcf')
	with outfile.open('w') as fvcf:
		fvcf.write(VCFHEADER.format(samples = '\t'.join(samples)) + '\n')
		reader.rewind()
		for r in reader:
			mutation_ids = r.mutation_id.split(':')
			# tsv file doesn't have ref/alt alleles, we randomly assign
			bases = list('ATGC')
			ref = random.choice(bases)
			alt = random.choice(list(set(bases) - {ref}))
			records = [
				mutation_ids[2],
				mutation_ids[3],
				'.',
				ref,
				alt,
				'100',
				'PASS',
				'',
				'GT:AD:DP:CN']
			for sample in samples:
				if sample == r.variant_case:
					# we lost r.minor_cn
					records.append('%s:%s,%s:%s:%s' % (
						'0|0' if r.genotype == 'AA' else '1|1' if r.genotype == 'BB' else '0|1',
						r.ref_counts,
						r.var_counts,
						int(r.ref_counts) + int(r.var_counts),
						r.major_cn))
				else:
					records.append('./.:.:.:.')
			fvcf.write('\t'.join(records) + '\n')
	return outfile

def splitVcf(vcffile, outdir):
	pVcfSplit.input = vcffile
	pVcfSplit.exdir = outdir
	PyPPL().start(pVcfSplit).run({'ppldir': TMPDIR})

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print('Usage: %s <path_of_tsv_file>' % sys.argv[0])
		sys.exit(1)
	vcffile = convert2vcf(sys.argv[1])
	splitVcf(vcffile, Path(__file__).parent.parent.parent / 'tumhet')
