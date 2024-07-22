import torch
import transformers
from transformers import BertModel, BertTokenizer
from transformers import pipeline

print(torch.cuda.is_available())
device = 0 if torch.cuda.is_available() else -1







model = BertModel.from_pretrained('bert-base-uncased')

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

classifier = pipeline('text-classification', model='bert-base-uncased', device=device)

result = classifier("I love using Hugging Face models for NLP tasks!")
print(result)
