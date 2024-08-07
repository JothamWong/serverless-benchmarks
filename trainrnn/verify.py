from rnn import RNN
import torch

n_categories = 18
all_letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,;'-"
n_letters = 59
all_categories = ['Arabic', 'Chinese', 'Czech', 'Dutch', 'English', 'French', 'German', 'Greek', 'Irish', 'Italian', 'Japanese', 'Korean', 'Polish', 'Portuguese', 'Russian', 'Scottish', 'Spanish', 'Vietnamese']

rnn = RNN(n_letters, 128, n_letters, all_categories, n_categories, all_letters, n_letters)

model_path = "rnn_model.pth"
rnn.load_state_dict(torch.load(model_path))