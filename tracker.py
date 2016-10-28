
import numpy as np

from queue import Queue
from scipy.misc import imresize
from operator import add




class Tracker:
	"""
	Generic tracking model. A location is represented by an affine transformation (e.g., Xt−1), which warps the
	coordinate system so that the target lies within the unit square. Particles representing possible target locations Xt, 
	at time t are sampled according to P(Xt|Xt−1), which in this case is a diagonal-covariance Gaussian centered at Xt−1.
	
	Where:
	Xt = (xt, yt, θt, st, αt, φt)
	denote x, y translation, rotation angle, scale, aspect ratio, and skew direction at time t.

	P(Xt|Xt−1) = N (Xt; Xt−1, Ψ)
	where Ψ is a diagonal covariance matrix whose elements are the corresponding variances of affine parameters, assumes the variance of each affine parameter does not change over time

	See 3.3.1 Dynamic model in http://www.cs.toronto.edu/~dross/ivt/RossLimLinYang_ijcv.pdf for reference

	Particle filter calss"""
	def __init__(self, init_location,):
		self.conf_q = Queue(maxsize=99999)
		self.loc_q = Queue(maxsize=99999)
		self.img_q = Queue(maxsize=99999)
		self.location = init_location
		self.params = self._init_params(init_location)
		print('i am new!')



	def _init_params(self, init_location):
		"""Initialize tracker's parameters"""

		params = {'p_sz': 64, 'p_num': 20000, 'min_conf': 0.2, 
				'mv_thr': 0.1, 'up_thr': 0.35, 'roi_scale': 2}
		diag_s = np.ceil((init_location[2]**2 + init_location[3]**2)**0.5/7)
		params['aff_sig'] = [diag_s, diag_s, 0.004, 0.0, 0.0, 0]
		params['ratio'] = init_location[2] / params['p_sz']
		
		return params

	def _qs_full(self):
		if self.conf_q.full() and self.pre_M_q.full():
			return True
		else:
			return False

	def gen_best_records(self, inter_steps=20):
		"""Returns the best records in last `inter_steps` steps."""
		confs = [self.conf_q.get() for _ in range(inter_steps)]
		imgs = [self.img_q.get() for _ in range(inter_steps)]
		locs = [self.loc_q.get() for _ in range(inter_steps)]
		idx = np.argmax(confs)
		return imgs[idx], locs[idx]


	def draw_particles(self):
		"""
		Generates particles according to 
		P(Xt|Xt−1) = N (Xt; Xt−1, Ψ)

		Args:
			aff_params: affine parameters, see class doc string for 
				specific element definition.
				[cx, cy, w/p_sz, 0, h/w, 0] for 6 degrees of freendom
				[tlx, tly, w, h] for 4 degrees of freedom.
				.
		Returns:
			aff_params_M : self.p_num*dof size matrix,
				where rows are updated randomly drawed affine 
				params, columns repersent each particles. 
		"""
		pass



	def predict_location(self, pre_M, gt_last, rz_factor, t):
		"""
		Predict location for each particle. It is calculated by
		1. compute the confidence of the i-th candidate, which is 
			the summation of all the heatmap values within the candidate region.
		2. the candidate with the highest confidence value is predicted as target.

		Args:
			img_siz: tuple(image height, image width)
			pre_M: predicted heat map
			t: index of current frame
		"""
		pass


	def get_most_conf_M(self):
		"""Returns the most confidence heat maps."""

		# Pull self.conf_records all out, and retrive 
		# the most confident heat map. 

		return updated_gt_M


	def linear_prediction(self):
		"""
		Predicts current location linnearly according
		to las two frames location. This may boost the 
		robustnesss of obejct blocking.
		"""
		pass

	def distracted(self):
		"""Distracter detection."""

		# up-sampling pre_M

		# Compute confidence according to 
		# S = with_in / with_out
		conf_within = self.compute_conf(self.pre_M_resized, self.best_p_i_loc)
		conf_all = np.sum(self.pre_M_resized)
		distracter_score = conf_within / conf_all
		print('The probability of been distracted is %s'%distracter_score)
		if distracter_score > self.params['min_conf']:
			return False
		else:
			return True
			
	@classmethod # Tested
	def compute_conf(self, roi, roi_sum, loc_p):
		"""Helper func for computing confidence.
		
		Args:
			roi: extracted roi.
			loc_p: list, location params [cx, cy, w, h] in roi space
		Returns:
			conf: int, sum of values with the region specified by loc_p
	
		"""
		x,y,w,h = loc_p
		conf = np.sum(roi[y-int(0.5*h): y+int(0.5*h), \
					x-int(0.5*w):x+int(0.5*w)])
		conf = conf / (roi_sum - conf) # within/all ratio
		return conf

	@classmethod
	def aff2loc(self, las_loc, aff_param, rz_factor):
		"""Convert affine params to location."""
		assert len(aff_param)==4, 'This method only works for dof 4 aff space.'
		# Space transformation, scalling and displacement
		aff_param /= rz_factor 
		cur_loc = [i+j for i,j in zip(las_loc, aff_param)]
		return cur_loc


class TrackerVanilla(Tracker):
	"""Vanilla tracker

		The covariance matrix has only 4 degrees of freedom,
		specified by vertical, horizontal translation of the central
		point, variance of the width, variance of the w/h ratio.

		The corrresponding actual senarios are object replacment,
		object zoom in/out, object rotaion. Should be sufficient 
		for most cases of car tracking.

	"""
	def __init__(self, init_location):
		super(TrackerVanilla, self).__init__(init_location)
		self._update_params()

	def _update_params(self):
		"""Update aff_sig param."""
		self.params['aff_sig'] = [10, 10, 0.05, 0.05]
		self.params['particle_scales'] = np.arange(0.1, 5., 0.5)       

	# Tested
	def draw_particles(self):
		"""
		The covariance matrix has only 4 degrees of freedom,
		specified by vertical, horizontal translation of the central
		point, variance of the width, variance of the w/h ratio.

		The corrresponding actual senarios are object replacment,
		object zoom in/out, object rotaion. Should be sufficient 
		for most cases of car tracking.

		"""
		# Define degrees of freedom 
		dof = len(self.params['aff_sig'])

		# Construct an p_num*6 size matrix with with each 
		# column repersents one particle

		#aff_params_M = np.kron(np.ones((self.params['p_num'],1)), np.array(aff_params))

		# First onstruct a p_num*dof size normal distribution with 
		# mean 0 and sigma 1
		rand_norml_M = np.array([np.random.standard_normal(dof) for _ in range(self.params['p_num'])])

		# Then construct a affine sigma matrix
		aff_sig_M = np.kron(np.ones((self.params['p_num'], 1)), self.params['aff_sig'])

		# Update particles 
		aff_params_M = rand_norml_M * aff_sig_M

		tmp = np.copy(aff_params_M)
		for s in range(self.params['particle_scales']):#, 1.4, 1.6, 1.8, 2.]:
			scale_M = np.copy(tmp)
			aff_params_M = np.vstack((aff_params_M, scale_M))
		self.aff_params_M = aff_params_M
		return aff_params_M


	def predict_location(self, pre_M, gt_last, rz_factor, img, roi_size=224):
		"""
		Predict location for each particle. It is calculated by
		1. compute the confidence of the i-th candidate, which is 
			the summation of all the heatmap values within the candidate region.
		2. the candidate with the highest confidence value is predicted as target.

		Args:
			pre_M: (224,224) array, predicted heat map.
			gt_last: [tlx, tly, w, h], location of the last frame.
			rz_factor: >1 int, scalling factor, pixel in roi / pixel in img.
			img: image array, used for put into Q
		"""
		# transform self.aff_params_M to location_M with each column 
		# repersent [cx, cy, w, h] in the pre_M heat map
		loc_M = np.zeros(self.aff_params_M.shape)
		_, _, w, h = gt_last
		cx, cy = roi_size // 2, roi_size // 2
		loc_M[:, 0] = cx
		loc_M[:, 1] = cy
		loc_M[:, 2] = rz_factor * w 
		loc_M[:, 3] = rz_factor * h
		#self.aff_parms_M[:, 2] *= w
		#self.aff_parms_M[:, 3] *= h
        


		idx = self.params['p_num']
		for s in self.params['particle_scales']:
			#loc_M[idx: idx+idx, 2] *= s
			#loc_M[idx: idx+idx, 3] *= s
			self.aff_parms_M[idx: idx+idx, 2] *= s
			self.aff_parms_M[idx: idx+idx, 3] *= s
			idx += idx

		loc_M += self.aff_params_M


		loc_M = loc_M.astype(np.int)

		assert pre_M.shape == (224,224)

		# Compute conf for each particle 
		conf_lsit = []
		pre_sum = pre_M.sum()
		for p_i_loc in loc_M:
			conf_i = self.compute_conf(pre_M, pre_sum, p_i_loc)
			conf_lsit += [conf_i]

		# Get index and conf score of of the most confident one
		idx = np.argmax(conf_lsit)
		self.cur_best_conf = conf_lsit[idx]

		# Store values for computing distraction 
		self.best_p_i_loc = loc_M[idx]
		self.pre_M = pre_M

		# Get the corresponding aff_param which is then
		# used to predicted the cureent best location
		best_aff =  self.aff_params_M[idx]
		self.pre_location = self.aff2loc(gt_last, best_aff, rz_factor)

		# Stack into records queue
		self.loc_q.put(self.pre_location)
		self.conf_q.put(self.cur_best_conf)
		self.img_q.put(img)

		return self.pre_location










		

