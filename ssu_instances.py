from datetime import datetime
from ssu import *

class SSU_Natural(SSU):

	base_heating_setpt = 60
	base_cooling_setpt = 90

	def generate_schedule(self, temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time):
		heating_setpt = self.base_heating_setpt
		cooling_setpt = self.base_cooling_setpt
		# determine the new setpts, then check if temp falls outside of them
		#1. Check time of day
		dt = datetime.fromtimestamp(time // 1000000000)
		#year, month, day, hour, minute, second, microsecond, and tzinfo.

		#2. If hour is between 7 and 22, use regular window. Expand if not.
		if dt.hour < 7 or dt.hour > 22:
			heating_setpt = int(base_heating_setpt + (base_heating_setpt * 0.5))
			cooling_setpt = int(cooling_setpt - (base_cooling_setpt * 0.5))

		return temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time
		

class SSU_Social(SSU):
	
	def generate_schedule(self, temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time):
		dt = datetime.fromtimestamp(time // 1000000000)

		if dt.weekday() >= 5: #it's a weekend
			heating_setpt += int(0.5 * heating_setpt)
			cooling_setpt -= int(0.5 * cooling_setpt)

		return temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time

class SSU_Custom(SSU):
	def generate_schedule(self, temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time):
		dt = datetime.fromtimestamp(time // 1000000000)

		if dt.month == 12 and (dt.day >= 20 and dt.day <= 31): #Going on vacation
			heating_setpt = -200 
			cooling_setpt = 200

		return temp, rel_humidity, heating_setpt, cooling_setpt, override, fan, mode, state, time
