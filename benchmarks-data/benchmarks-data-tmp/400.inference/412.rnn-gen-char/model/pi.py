import pickle

params = {
    "n_categories": 18,
    "all_letters": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,;'-",
    "n_letters": 59,
    "all_categories": ['Arabic', 'Chinese', 'Czech', 'Dutch', 'English', 'French', 'German', 'Greek', 'Irish', 'Italian', 'Japanese', 'Korean', 'Polish', 'Portuguese', 'Russian', 'Scottish', 'Spanish', 'Vietnamese']
}

with open('rnn_params.pkl', "wb") as handle:
    pickle.dump(params, handle)

with open('rnn_params.pkl', 'rb') as handle:
    b = pickle.load(handle)

print(params == b)