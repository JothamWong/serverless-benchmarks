import rnn
import torch

all_categories = ['Arabic', 'Chinese', 'Czech', 'Dutch', 'English', 'French', 'German', 'Greek', 'Irish', 'Italian', 'Japanese', 'Korean', 'Polish', 'Portuguese', 'Russian', 'Scottish', 'Spanish', 'Vietnamese']
all_letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,;'-"
model = rnn.RNN(59, 128, 59, all_categories, 18, all_letters, 59)
model.load_state_dict(torch.load("rnn_model.pth"))
model.eval()
