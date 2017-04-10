from abc import ABCMeta, abstractmethod

class SSU(object):
	"""
	Single Schedule Unit
	This is the abstract base class 
	Contains the logic for a schedule of a specific type. Examples include time-based and calendar-based schedules.
	"""

	__metaclass__ = ABCMeta

	@abstractmethod
	def generate_schedule(self, temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time):
		pass

class SSU_Link(object):
	"""
	Linked list object that contains an Single Schedule Unit (SSU).
	"""

	def __init__(self, ssu, rest=None):
		self.ssu = ssu
		self.rest = rest

	@classmethod
	def create_ssu_list(cls, ssu_list):
		lst = None
		for ssu in ssu_list[::-1]:
			lst = SSU_Link(ssu, lst)
		return lst
