Preprocessing: 
MFCC feature size = 30 
512 is wavetable length  

WTSv2 model: 


Encode pitch,loudness and MFCC with MLPs of input size *in_size*, each layer with *hidden_size* perceptrons and a total of *n_layers* dense/fully-connected layers. Each hidden layer of *n_layers* is fully connected with the input and subsequent hidden layers, with a layer normalisation and a LeakyReLU activation applied at each step. 

GRU with *in_size* 30 (MFCC features), each hidden layer of dim 512. 


MFCC(30 features initially) is encoded via LayerNorm(30), GRU(30,512), and a linear reduction layer (to 16 dims).
Pitch, loudness, and MFCC (now 16-dim) are each passed through their own MLPs (of hidden_size).
These three outputs are concatenated into a single feature vector (hidden_size * 3).
This concatenated feature is passed through a GRU (to add temporal context).
The GRU output and the original concatenated features are concatenated (hidden_size + hidden_size * 3 = hidden_size * 4).
This is fed to out_mlp (input: hidden_size * 4, output: hidden_size), which further processes the combined features for the next stages of synthesis.