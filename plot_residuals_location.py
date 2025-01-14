import numpy as np
import pickle
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def clean_roi(roi_vals, roi_labels):
	roi_vals = roi_vals.reshape((len(roi_vals), ))
	final_roi_labels = []
	for val_index in roi_vals:
		if val_index == 0:
			final_roi_labels.append("other")
		else:
			final_roi_labels.append(roi_labels[val_index-1][0][0])
	return final_roi_labels

def clean_atlas(atlas_vals, atlas_labels):
	at_vals = atlas_vals.reshape((len(atlas_vals), ))
	at_labels = []
	for val_index in at_vals:
		at_labels.append(atlas_labels[val_index-1][0][0])
	return at_labels

def plot_atlas(df, file_name):
	all_residuals = list(df.residuals)
	g = sns.catplot(x="residuals", y="atlas_labels", data=df, height=17.5, aspect=1.5)
	g.set_xticklabels(rotation=90)
	g.set(xlim=(min(all_residuals), max(all_residuals)))
	g.set_axis_labels("residuals", "location")
	plt.title("Residuals in all Brain Regions")
	plt.savefig("../visualizations/" + str(file_name) + ".png")
	# plt.show()
	return

def plot_roi(df, file_name):
	all_residuals = list(df.residuals)
	g = sns.catplot(x="residuals", y="roi_labels", data=df, height=7.5, aspect=1.5)
	g.set_xticklabels(rotation=90)
	g.set(xlim=(min(all_residuals), max(all_residuals)))
	g.set_axis_labels("residuals", "location")
	plt.title("Residuals in all Language Regions")
	plt.savefig("../visualizations/" + str(file_name) + ".png")
	return

def main():
	if len(sys.argv) != 2:
		print("usage: python plot_residuals_locations.py -residual")
		# example: python plot_residuals_locations.py ../residuals/concatenated_all_residuals.p
		exit()

	# get residuals
	residual_file = sys.argv[1]
	file_name = residual_file.split("/")[-1].split(".")[0]
	all_residuals = pickle.load( open( residual_file, "rb" ) )

	# get atlas and roi
	atlas_vals = pickle.load(open("../brain_data/subj1/atlas_vals.p", "rb" ) )
	atlas_labels = pickle.load(open("../brain_data/subj1/atlas_labels.p", "rb" ) )
	roi_vals = pickle.load( open("../brain_data/subj1/roi_vals.p", "rb" ) )
	roi_labels = pickle.load(open("../brain_data/subj1/roi_labels.p", "rb" ) )

	final_roi_labels = clean_roi(roi_vals, roi_labels)
	at_labels = clean_atlas(atlas_vals, atlas_labels)

	# make dataframe
	df_dict = {'voxel_index': list(range(len(all_residuals))),
			'residuals': all_residuals,
			'atlas_labels': at_labels,
			'roi_labels': final_roi_labels}

	df = pd.DataFrame(df_dict)

	plot_roi(df, file_name + "-roi")
	plot_atlas(df, file_name + "-atlas")

	print("done.")

	return

if __name__ == "__main__":
    main()
