#!/usr/bin/env python
"""Generate meta file"""
from pathlib import Path
from remotedata import sha1, metafile

def nameskip(path):
	return not path.name \
		or path.name.startswith('.') \
		or path.name.endswith('.meta') \
		or path.name == 'workdir'

class File:

	def __init__(self, path):
		self.path   = Path(path)
		self.meta   = Path(metafile(str(path)))
		self._mtime = self.path.stat().st_mtime

	@property
	def mtime(self):
		return self._mtime

	def needUpdate(self):
		if not self.meta.exists():
			return True
		if self.meta.stat().st_mtime < self.mtime:
			return True
		return False

	def sha(self):
		if self.needUpdate():
			return sha1(self.path)
		return self.meta.read_text().strip().split("|")[1]

	def updateMeta(self):
		print('Updating meta of %s ... ' % self.path)
		self.meta.write_text('%s|%s' % (self.mtime, self.sha()))

class Dir(File):

	@property
	def mtime(self):
		for path in self.path.glob('*'):
			if path.is_dir() or nameskip(path):
				continue
			mtime = Dir(path)._mtime if path.is_dir() else path.stat().st_mtime
			self._mtime = max(self._mtime, mtime)
		return self._mtime

	def needUpdate(self):
		ret = super().needUpdate()
		if ret:
			return ret
		meta_mtime = self.meta.stat().st_mtime
		return self.mtime > meta_mtime

	def updateMeta(self):
		if self.path.name:
			super().updateMeta()
		for path in self.path.glob('*'):
			if nameskip(path):
				continue
			if path.is_dir():
				path = Dir(path)
			else:
				path = File(path)
			if path.needUpdate():
				path.updateMeta()

if __name__ == "__main__":
	Dir(Path(__file__).parent.parent).updateMeta()
