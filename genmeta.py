"""Generate meta file"""
from pathlib import Path
from remotedata import sha1, metafile

def nameskip(name):
	return not name or name.startswith('.') or name.endswith('.meta') or name == Path(__file__).name

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
		ret = 0
		for path in self.path.glob('*'):
			if path.is_dir() or nameskip(path.name):
				continue
			ret = max(ret, File(path).mtime)
		return ret

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
			if nameskip(path.name):
				continue
			if path.is_dir():
				path = Dir(path)
			else:
				path = File(path)
			if path.needUpdate():
				path.updateMeta()

if __name__ == "__main__":
	Dir('.').updateMeta()
