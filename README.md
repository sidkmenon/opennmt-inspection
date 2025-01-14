# OpenNMT-py with inspection & sentence representation

## OpenNMT-py modifications
This is a modification of a OpenNMT-py fork that creates sentence representations in a MAT file. The following scripts have been added. Your sentence representations must be formatted such that each sentence is on a new line; an example format is included in `examplesGLM.txt`. The flags mentioned below for `separate-layers` and `dump-layers` must be true when running `train.py` and `translate.py`, respectively.

```
-get_dict.py
  Find words present in your sentence data but not the source training vocab after preprocess.py. Includes corresponding sentence and all missing words with its occurrences.
  Usage: python get_dict.py -sentences.txt -EXAMPLE.vocab.pt
```

Sentence representations are created for elementwise (1) average, (2) maximum, (3) minimum, and (4) last word of all words in the sentence. Each word embedding is of length 500.

```
-create_sentence_representation.py
  Creates MAT files of consisting of an array of shape (sentences) x (boolean, sentence embedding) for a single layer. Boolean is 1 if all words in sentence are in training vocabulary, and 0 if otherwise.
  Usage: python create_sentence_representation.py -sentences.txt -EXAMPLE.vocab.pt -EXAMPLE.pred.pt -num_layers
```

File names are saved as <b>"model name" + "which layer" + "method"</b> in the <b>embeddings/model/method</b> directory. Each MAT file has the same number of structs in the sentence data, labelled as <i>"sentenceX"</i> corresponding to (1) the boolean of if the all the words in the sentence are present in training + (2) the embedding of the Xth sentence based on order of the sentences in the txt file. The boolean is 1 if we are not missing any words, and 0 if otherwise. An example representation in the MAT file is `sentence1: [ 1, .123, .123, .123 ...]` with length 501.

## Corpus multiparallization
Multiparallelization of parallel corpora for machine translation.

```
-multiparallelize_text.py
  Returns multiparallelization text files given parallel translation pairs (source and target languages files). Saves files in one upstream directory "../multiparallelize/" as "parallel-src.txt" and all "parallel-target" text files.
  Usage: python multiparallelize_text.py -srclangAB.txt -tgtlangAB.txt -srclangAC.txt -tgtlangAC.txt (as many src languages texts of src-tgt pairs)
```

## Decoding (updating)
Batching used for Odyssey:
```
-odyssey_decoding.py
  Linear decoding of fMRI brain activations (240xN) to OpenNMT embeddings (240x500) where N is the number of voxels in a specified spherical spotlight (default: 5 voxels).
  Usage: python odyssey_decoding.py -embedding_layer -embedding -title -batch_num -total_batches
```

Original scratch code + others in `decoding.py`.

### Odyssey cluster batching (updating)
Parallel threads initially attempted. TBD in `decoding.py` and `odyssey_decoding.py`. Switched to job batching. See `odyssey_decoding.py`.

Script used to generate for all possible models:
```
-make_scripts.py
  Specify which models to make bash scripts when given the number of batches desired.
  Usage: python make_scripts.py -language -num_layers -type -which_layer -agg_type -subj_num -num_batches
```

## Residuals (updating)
### Concatenating residual batches
```
-get_residuals.py
  Concatenating residuals from all batches
  Usage: python get_residuals.py -residual_name -total_batches
```

### Plotting
Visualizing relationship between residuals from linear decoding and region of brain.

```
-plot_residuals_locations.py
  Plots brain atlas ROI and language ROI against residual against per subject and saves images.
  Usage: python plot_residuals_locations.py -residual
  Example: python plot_residuals_locations.py ../residuals/concatenated_all_residuals.p
```

Also included in `residual_visualization.ipynb`.

# Step-by-Step Walkthrough to generate Graphs

There are three main phases to this project. First, translation data is used to create an NLP Model. Then the model's embeddings are captured on a prediction text ('examplesGLM.txt'). Then the embeddings are regressed & processed with brain activations. Finally the RMSEs from this regression are visualized.

## Phase 1: Training NLP Models & Inference on Text

The translation data can be found at [this link](http://www.statmt.org/wmt16/translation-task.html) to the Europarl v7 corpus. After downloading via a preferred method, the corpus must first be multiparallelized (so that sentence *i* in the Czech, English, Spanish, etc. corpus all refer to the same idea). For example, one might run:
```
python multiparallelize_text.py ../corpus-data/czech/europarl-v7-en-cs.txt ../corpus-data/czech/europarl-v7-cs-en.txt ../corpus-data/spanish/europarl-v7-en-es.txt ../corpus-data/spanish/europarl-v7-es-en.txt
```
After saving the corpus data into a directory called corpus-data, and sorting into czech, spanish, etc. subfolders. Validation data also needs to be produced, which can be simply created by:
```
./make_validation.sh
```
Modify the variable *validation_num_lines* in ```make_validation.sh``` to be at ~5000 for good training results (see **step 2**) if you train on a large enough corpus for this to be possible.

Next, we first create the NLP model based on the translation data, and then we save its embeddings on our prediction text. For example, we could choose to create a Spanish translation NLP model:
```
python preprocess.py -train_src ../multiparallelize/training/parallel_src-training.txt  -train_tgt -valid_src -valid_tgt -save ../multiparallelize
```
This produces, as per below, ```multiparallelize.train.pt, multiparallelize.val.pt,``` and ```multiparallelize.vocab.pt```. We then take these *.pt* files and train (using the **--separate_layers** flag)

Then we take the

## Phase 2: Regressing to Brain Data
We need to download the brain fMRI scans (in this case, of ```examplesGLM.txt```). The fMRI scans are found [here](https://drive.google.com/drive/folders/1dfwmC6F8FuXlz_3fu2Q1SiSsZR_BY8RP) (you can use [this link](https://github.com/circulosmeos/gdown.pl) to download from drive via curl, wget, etc. ) *Note in the codebase we only regress to subject 1's embeddings because of computational tractability, but this is easily amended* (in ```odyssey_decoding.py``` and ```make_scripts.py```)
If you want, you can skip the earlier steps and download the NLP model embeddings from [this link](https://drive.google.com/drive/folders/1LNdXXD-W8ebm8WD1oIMKSw6Nt9rqsuWQ).
If you have the embeddings already, we still need to convert the subjects' fMRI data (in *.mat* format) into a more readable *.p* format; run
```
python format_for_subject.py --subject_number [X1 X2 X3]
```
Where ```X``` is the number of the subject whose *.mat* file you intend to process; note you can process one or more subjects at a time by listing multiple subject numbers (default is just the first subject (subject 1)). Type
```
python format_for_subject.py --help
```
for more.

We recommend use of a supercomputing cluster to do the regression step.
Run
```
python make_scripts.py
```
To make scripts in an upstream directory; then one can use a simple bash script to run everything in this folder, e.g. (for Slurn)
```
#!/bin/bash


for num in `seq 0 99`; do
  for layer_num in `seq 1 2`; do
    for agg_type in min max avg last; do
      sbatch "subj1_decoding_${num}_of_100_parallel-english-to-spanish-model-2layer-brnn-pred-layer${layer_num}-${agg_type}.sh" -H
    done
  done
done
```

Now run

```
python get_residuals.py --residual_name XXXXX --total_batches X
```
Where ```residual_name``` is the stub of the residuals that you are looking to combine (from the ```/residuals```) folder and ```total_batches``` is the total number of residual batches that were processed by the cluster for the residual stub (default 100). 

## Phase 3: Plotting

Now simply follow the instructions from above to plot the residuals, etc.



# OpenNMT-py with inspection

This is a fork of OpenNMT-py that allows for inspection of the activations of intermediate neurons, as well as manual modification of those neurons at inference time. Everything is known to work with the single-direction RNN encoder; others have not been tested. This fork adds the following option to `train.py`:

```
-separate_layers
  Train the RNN or BRNN with a separate module for each layer. This must be true at training time in order for -dump_layers to work at inference time.
```

It adds the following option to `translate.py`:

```
-dump_layers FILENAME
  Dump the activations of all encoder layers to FILENAME. Only works on models trained with -separate_layers (or non-RNN models, theoretically). The file will be in .pt format, consisting of an array of shape (sentences) x (tokens in this sentence) x (layers) x (neurons in this layer), where only the last dimension of the array is a Tensor.
```

It adds the `correlate.py` and `correlation-to-basis.py` scripts in the `searchers/` directory. These aren't easy to use yet, but they provide functions that can be called from Python, with a usage example at the bottom of `correlate.py`.

It also adds the script `mask_out.py` in the root directory. This is run with the following options:

```
-mask_out_layer INT
  Which layer to apply masking out to
-mask_out_basis FILENAME
  A .pt file containing a (# of neurons in this layer) x (# neurons in this layer) matrix, where the (n)th row is the
  hypothesized (n)th most important basis vector for the space. When testing individual neurons' importances, this will be
  a permutation matrix. The basis must be orthonormal.
-mask_out_cumulative
  Use this flag to do the cumulative experiment, where more neurons are masked out at every step. If this is not set, then
  instead each interval will be masked out independently (i.e. there will be a run without 0-50, then without 50-100, etc.)
-mask_out_intervals INT
  The number of intervals to divide the basis into. E.g. if this is 10, and there are 500 neurons, then at every step 50 more neurons
  will be masked out.
```

`mask_out.py` also accepts all the same arguments as `translate.py`. When running `mask_out.py`, the `-output` option should specify a directory, and this directory will be populated with files named `without-%d-%d.txt` with the two integers indicating which range of basis vectors was masked out. Currently, `-dump_layers` will not work, as every next run will overwrite the dump. This will hopefully be fixed soon.

The README from upstream OpenNMT-py follows.

# OpenNMT-py: Open-Source Neural Machine Translation

[![Build Status](https://travis-ci.org/OpenNMT/OpenNMT-py.svg?branch=master)](https://travis-ci.org/OpenNMT/OpenNMT-py)

This is a [Pytorch](https://github.com/pytorch/pytorch)
port of [OpenNMT](https://github.com/OpenNMT/OpenNMT),
an open-source (MIT) neural machine translation system. It is designed to be research friendly to try out new ideas in translation, summary, image-to-text, morphology, and many other domains.

Codebase is relatively stable, but PyTorch is still evolving. We currently only support PyTorch 0.4 and recommend forking if you need to have stable code.

OpenNMT-py is run as a collaborative open-source project. It is maintained by [Sasha Rush](http://github.com/srush) (Cambridge, MA), [Ben Peters](http://github.com/bpopeters) (Saarbrücken), and [Jianyu Zhan](http://github.com/jianyuzhan) (Shanghai). The original code was written by [Adam Lerer](http://github.com/adamlerer) (NYC).
We love contributions. Please consult the Issues page for any [Contributions Welcome](https://github.com/OpenNMT/OpenNMT-py/issues?q=is%3Aissue+is%3Aopen+label%3A%22contributions+welcome%22) tagged post.

<center style="padding: 40px"><img width="70%" src="http://opennmt.github.io/simple-attn.png" /></center>


Table of Contents
=================
  * [Full Documentation](http://opennmt.net/OpenNMT-py/)
  * [Requirements](#requirements)
  * [Features](#features)
  * [Quickstart](#quickstart)
  * [Citation](#citation)

## Requirements

All dependencies can be installed via:

```bash
pip install -r requirements.txt
```

Note that we currently only support PyTorch 0.4.

## Features

The following OpenNMT features are implemented:

- [data preprocessing](http://opennmt.net/OpenNMT-py/options/preprocess.html)
- [Inference (translation) with batching and beam search](http://opennmt.net/OpenNMT-py/options/translate.html)
- [Multiple source and target RNN (lstm/gru) types and attention (dotprod/mlp) types](http://opennmt.net/OpenNMT-py/options/train.html#model-encoder-decoder)
- [TensorBoard/Crayon logging](http://opennmt.net/OpenNMT-py/options/train.html#logging)
- [Source word features](http://opennmt.net/OpenNMT-py/options/train.html#model-embeddings)
- [Pretrained Embeddings](http://opennmt.net/OpenNMT-py/FAQ.html#how-do-i-use-pretrained-embeddings-e-g-glove)
- [Copy and Coverage Attention](http://opennmt.net/OpenNMT-py/options/train.html#model-attention)
- [Image-to-text processing](http://opennmt.net/OpenNMT-py/im2text.html)
- [Speech-to-text processing](http://opennmt.net/OpenNMT-py/speech2text.html)
- ["Attention is all you need"](http://opennmt.net/OpenNMT-py/FAQ.html#how-do-i-use-the-transformer-model)
- Inference time loss functions.

Beta Features (committed):
- multi-GPU
- Structured attention
- [Conv2Conv convolution model]
- SRU "RNNs faster than CNN" paper

## Quickstart

[Full Documentation](http://opennmt.net/OpenNMT-py/)


### Step 1: Preprocess the data

```bash
python preprocess.py -train_src data/src-train.txt -train_tgt data/tgt-train.txt -valid_src data/src-val.txt -valid_tgt data/tgt-val.txt -save_data data/demo
```

We will be working with some example data in `data/` folder.

The data consists of parallel source (`src`) and target (`tgt`) data containing one sentence per line with tokens separated by a space:

* `src-train.txt`
* `tgt-train.txt`
* `src-val.txt`
* `tgt-val.txt`

Validation files are required and used to evaluate the convergence of the training. It usually contains no more than 5000 sentences.


After running the preprocessing, the following files are generated:

* `demo.train.pt`: serialized PyTorch file containing training data
* `demo.valid.pt`: serialized PyTorch file containing validation data
* `demo.vocab.pt`: serialized PyTorch file containing vocabulary data


Internally the system never touches the words themselves, but uses these indices.

### Step 2: Train the model

```bash
python train.py -data data/demo -save_model demo-model
```

The main train command is quite simple. Minimally it takes a data file
and a save file.  This will run the default model, which consists of a
2-layer LSTM with 500 hidden units on both the encoder/decoder. You
can also add `-gpuid 1` to use (say) GPU 1.

### Step 3: Translate

```bash
python translate.py -model demo-model_acc_XX.XX_ppl_XXX.XX_eX.pt -src data/src-test.txt -output pred.txt -replace_unk -verbose
```

Now you have a model which you can use to predict on new data. We do this by running beam search. This will output predictions into `pred.txt`.

!!! note "Note"
    The predictions are going to be quite terrible, as the demo dataset is small. Try running on some larger datasets! For example you can download millions of parallel sentences for [translation](http://www.statmt.org/wmt16/translation-task.html) or [summarization](https://github.com/harvardnlp/sent-summary).

## Pretrained embeddings (e.g. GloVe)

Go to tutorial: [How to use GloVe pre-trained embeddings in OpenNMT-py](http://forum.opennmt.net/t/how-to-use-glove-pre-trained-embeddings-in-opennmt-py/1011)

## Pretrained Models

The following pretrained models can be downloaded and used with translate.py.

http://opennmt.net/Models-py/



## Citation

[OpenNMT technical report](https://doi.org/10.18653/v1/P17-4012)

```
@inproceedings{opennmt,
  author    = {Guillaume Klein and
               Yoon Kim and
               Yuntian Deng and
               Jean Senellart and
               Alexander M. Rush},
  title     = {Open{NMT}: Open-Source Toolkit for Neural Machine Translation},
  booktitle = {Proc. ACL},
  year      = {2017},
  url       = {https://doi.org/10.18653/v1/P17-4012},
  doi       = {10.18653/v1/P17-4012}
}
```
