import scipy.io
from tqdm import tqdm
import pickle
import numpy as np
import sys
import math
from scipy.linalg import lstsq
from sklearn.model_selection import KFold
import argparse

# get initial information from MATLAB
def get_activations(info):
	print("getting activations...")
	mat = scipy.io.loadmat(info)

	activations = mat["examples_sentences"]
	volmask = mat["volmask"]
	atlasvals = mat["multimask_aal"]
	roi_labels = mat["labels_langloc"]
	atlas_labels = mat["labels_aal"]


	print("writing to file...")
	pickle.dump( activations, open( "../projects/opennmt-inspection/activations.p", "wb" ) )
	pickle.dump( volmask, open( "../projects/opennmt-inspection/volmask.p", "wb" ) )

	print("finished.")
	return activations, volmask

def chunkify(lst, num, total):
	if len(lst) % total == 0:
		chunk_size = len(lst) // total
	else:
		chunk_size = len(lst) // total + 1
	start = num * chunk_size
	if num != total - 1:
		end = num * chunk_size + chunk_size
	else:
		end = len(lst)
	return lst[start:end]

def all_activations_for_all_sentences(modified_activations, volmask, embed_matrix, num, total_batches, radius=5, do_cross_validation=False, kfold_split=10, do_pca=False):
	print("getting activations for all sentences...")
	# per_sentence = []
	res_per_spotlight = []
	a,b,c = volmask.shape
	nonzero_pts = np.transpose(np.nonzero(volmask))

	# iterate over spotlight
	print("for each spotlight...")

	index=0
	for pt in tqdm(chunkify(nonzero_pts, num, total_batches)):

		# SPHERE MASK BELOW
		sphere_mask = np.zeros((a,b,c))
		x1,y1,z1 = pt
		for i in range(-radius, radius+1):
			for j in range(-radius, radius+1):
				for k in range(-radius, radius+1):
					xp = x1 + i
					yp = y1 + j
					zp = z1 + k
					pt2 = [xp,yp,zp]
					if 0 <= xp and 0 <= yp and 0 <= zp and xp < a and yp < b and zp < c:
						dist = math.sqrt(i ** 2 + j ** 2 + k ** 2)
						if pt2 in nonzero_pts and dist <= radius:
							sphere_mask[x1+i][y1+j][z1+k] = 1
		# SPHERE MASK ABOVE

		spotlights = []

		# iterate over each sentence
		for sentence_act in modified_activations:
			spot = sentence_act[sphere_mask.astype(bool)]
			remove_nan = np.nan_to_num(spot)
			spotlights.append(remove_nan)

		## DECODING BELOW
		res = linear_model(embed_matrix, spotlights, do_cross_validation, kfold_split)
		print("RES for SPOTLIGHT #", index, ": ", res)
		res_per_spotlight.append(res)
		index+=1
		## DECODING ABOVE

	return res_per_spotlight

def linear_model(embed_matrix, spotlight_activations, do_cross_validation, kfold_split):
	if do_cross_validation:
		kf = KFold(n_splits=kfold_split)
		errors = []
		for train_index, test_index in kf.split(X):
			X_train, X_test = embed_matrix[train_index], embed_matrix[test_index]
			y_train, y_test = spotlight_activations[train_index], spotlight_activations[test_index]
			p, res, rnk, s = lstsq(X_train, y_train)
			residuals = np.sqrt(np.sum((y_test - np.dot(X_test, p))**2))
			errors.append(residuals)
		return np.mean(errors)
	p, res, rnk, s = lstsq(embed_matrix, spotlight_activations)
	residuals = np.sqrt(np.sum((spotlight_activations - np.dot(embed_matrix, p))**2))
	return residuals

def get_modified_activations(activations):
	i,j,k = volmask.shape
	nonzero_pts = np.transpose(np.nonzero(volmask))
	modified_activations = []
	for sentence_activation in tqdm(activations):
		one_sentence_act = np.zeros((i,j,k))
		for pt in range(len(nonzero_pts)):
			x,y,z = nonzero_pts[pt]
			one_sentence_act[int(x)][int(y)][int(z)] = sentence_activation[pt]
		modified_activations.append(one_sentence_act)
	pickle.dump( modified_activations, open( "modified_activations.p", "wb" ) )
	return modified_activations

def get_embed_matrix(embedding):
	dict_keys = list(embedding.keys())[3:]
	embed_matrix = np.array([embedding[i][0][1:] for i in dict_keys])
	in_training_bools = np.array([embedding[i][0][0] for i in dict_keys])
	return embed_matrix

def main():
	argparser = argparse.ArgumentParser(description="Decoding (linear reg). step from NN to brain")
	argparser.add_argument('--embedding_layer', type=str, help="Location of NN embedding (for a layer)", required=True)
	# argparser.add_argument("--subject_mat_file", type=str, help=".mat file ")
	argparser.add_argument("--subject_number", type=int, default=1, help="subject number (fMRI data) for decoding")
	argparser.add_argument("--batch_num", type=int, help="batch number of total (for scripting) (out of --total_batches)", required=True)
	argparser.add_argument("--total_batches", type=int, help="total number of batches", required=True)
	args = argparser.parse_args()

	# if len(sys.argv) != 6:
	# 	print("usage: python odyssey_decoding.py -embedding_layer -examplesGLM.mat -title -batch_num -total_batches")
	# 	exit()
	embed_loc = args.embedding_layer
	file_name = embed_loc.split("/")[-1].split(".")[0]
	embedding = scipy.io.loadmat(embed_loc)
	embed_matrix = get_embed_matrix(embedding)
	# info = sys.argv[2]
	# title = sys.argv[3]
	subj_num = args.subject_number
	num = args.batch_num
	total_batches = args.total_batches

	# saved = True
	# if not saved:
	# 	activations, volmask = get_activations(info)
	# 	print("saved activations.")
	# 	modified_activations = get_modified_activations(activations)
	# 	print("saved modified activations.")
	# else:
	# 	print("loading activations and mask...")
	# 	# activations = pickle.load( open( "activations.p", "rb" ) )
	# 	# volmask = pickle.load( open( "volmask.p", "rb" ) )
	# 	# modified_activations = pickle.load( open( "modified_activations.p", "rb" ) )
	activations = pickle.load( open( f"../examplesGLM/subj{subj_num}/activations.p", "rb" ) )
	volmask = pickle.load( open( f"../examplesGLM/subj{subj_num}/volmask.p", "rb" ) )
	modified_activations = pickle.load( open( f"../examplesGLM/subj{subj_num}/modified_activations.p", "rb" ) )

	all_residuals = all_activations_for_all_sentences(modified_activations, volmask, embed_matrix, num, total_batches)
	pickle.dump( all_residuals, open("../residuals/"+ str(file_name) + "_residuals_part" + str(num) + "of" + str(total_batches) + ".p", "wb" ) )
	print("done.")

	### RUN SIGNIFICANT TESTS BELOW

	### RUN SIGNIFICANCE TESTS ABOVE

	return

if __name__ == "__main__":
    main()
